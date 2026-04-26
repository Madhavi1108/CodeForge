import docker
import os
import tempfile
import time
import structlog
from typing import Dict, Any, Tuple

logger = structlog.get_logger()
client = docker.from_env()

LANGUAGE_CONFIG = {
    "python": {
        "image": "python:3.11-slim",
        "file_ext": ".py",
        "command": "python /tmp/script.py"
    },
    "cpp": {
        "image": "gcc:12-bullseye",
        "file_ext": ".cpp",
        "command": "sh -c 'g++ /tmp/script.cpp -o /tmp/script && /tmp/script'"
    },
    "java": {
        # `openjdk:17-slim` no longer exists on Docker Hub; use Temurin JDK 17.
        "image": "eclipse-temurin:17-jdk-jammy",
        "file_ext": ".java",
        "command": "sh -c 'javac /tmp/Main.java -d /tmp && java -cp /tmp Main'"
    }
}

class SandboxExecutionError(Exception):
    pass

class TimeoutError(Exception):
    pass

def execute_code(language: str, code: str, timeout: int = 15) -> Tuple[str, str, int, float]:
    if language not in LANGUAGE_CONFIG:
        raise ValueError(f"Language {language} not supported.")
        
    config = LANGUAGE_CONFIG[language]
    image = config["image"]
    
    import tarfile
    import io
    
    file_name = "Main.java" if language == "java" else f"script{config['file_ext']}"
    
    tar_stream = io.BytesIO()
    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
        tarinfo = tarfile.TarInfo(name=file_name)
        code_bytes = code.encode('utf-8')
        tarinfo.size = len(code_bytes)
        tar.addfile(tarinfo, io.BytesIO(code_bytes))
    tar_stream.seek(0)
    
    start_time = time.time()
    container = None
    try:
        # Ensure the runtime image exists on the host Docker daemon.
        # Without this, `containers.create()` fails with "No such image" on first run.
        try:
            client.images.get(image)
        except docker.errors.ImageNotFound:
            logger.info("Pulling sandbox image on demand", image=image)
            client.images.pull(image)

        container = client.containers.create(
            image=image,
            command=config["command"],
            working_dir='/tmp',
            detach=True,
            network_mode="none",
            mem_limit="128m",
            nano_cpus=500000000,
            pids_limit=64,
            security_opt=["no-new-privileges:true"],
            cap_drop=["ALL"],
            user="1000:1000"
        )
        
        # Use /tmp since it is writable for non-root users across base images.
        container.put_archive('/tmp', tar_stream)
        container.start()
        
        result = container.wait(timeout=timeout)
        exit_code = result["StatusCode"]

        # Older docker-py versions don't support demux=True on logs().
        # Fetch stdout and stderr in separate calls instead.
        try:
            stdout_b, stderr_b = container.logs(stdout=True, stderr=True, demux=True)
            stdout = (stdout_b or b"").decode('utf-8', errors='replace')
            stderr = (stderr_b or b"").decode('utf-8', errors='replace')
        except TypeError:
            # demux kwarg not supported — fetch each stream independently.
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8', errors='replace')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8', errors='replace')
        
        end_time = time.time()
        return stdout, stderr, exit_code, (end_time - start_time) * 1000
        
    except docker.errors.ContainerError as e:
        raise SandboxExecutionError(f"Container error: {str(e)}")
    except docker.errors.APIError as e:
        raise SandboxExecutionError(f"Docker API Error: {str(e)}")
    except (TimeoutError, SandboxExecutionError):
        raise
    except Exception as e:
        end_time = time.time()
        if (end_time - start_time) >= timeout:
            raise TimeoutError("Execution timed out")
        raise SandboxExecutionError(f"System error: {str(e)}")
    finally:
        if container:
            try:
                container.kill()
            except Exception:
                pass
            try:
                container.remove(force=True)
            except Exception:
                pass
