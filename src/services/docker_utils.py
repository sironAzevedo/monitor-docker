import json
import subprocess

import docker

from src.services.config_utils import log_and_notify

class DockerUtils:
    def __init__(self):
        self.client_docker = docker.from_env()
        self.api_client = self.client_docker.api

    def get_all_containers_details_subprocess(self):
        result = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        headers = ["ID", "Nome", "Imagem", "Status"]
        data = []

        for line in lines:
            if not line:
                continue
            values = line.split('\t')
            status_text = values[3].lower()
            status = "running" if "up" in status_text else "stopped"
            container_info = dict(zip(headers, values))
            container_info["Status"] = status
            data.append(container_info)

        return headers, data

    def get_running_containers_details(self):
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"],
            capture_output=True, text=True
        )
        lines = result.stdout.strip().split('\n')
        headers = ["ID", "Nome", "Imagem", "Status"]
        data = [dict(zip(headers, line.split('\t'))) for line in lines if line]
        return headers, data

    def get_all_containers_details(self):
        containers = self.client_docker.containers.list(all=True)
        headers = ["ID", "Nome", "Imagem", "Status", "Criado em"]
        data = [
            [
                c.short_id,
                c.name,
                c.image.tags[0] if c.image.tags else "<sem tag>",
                c.status,
                c.attrs['Created'][:19].replace("T", " ")
            ]
            for c in containers
        ]
        return headers, data

    def get_docker_images_details(self):
        images = self.client_docker.images.list()

        headers = ["ID", "Repository", "Tag", "Tamanho"]
        data = []

        for image in images:
            # Algumas imagens podem não ter tags
            tags = image.tags if image.tags else ["<none>:<none>"]

            for tag in tags:
                repo, tag_value = tag.split(":") if ":" in tag else (tag, "<none>")
                size_mb = round(image.attrs["Size"] / (1024 * 1024), 2)

                data.append([
                    image.short_id.replace("sha256:", ""),
                    repo,
                    tag_value,
                    f"{size_mb} MB"
                ])

        return headers, data

    def get_container_details(self, container_id):
        result = subprocess.run(
            ["docker", "inspect", container_id],
            capture_output=True, text=True
        )
        try:
            details = json.loads(result.stdout)[0]
            formatted_details = json.dumps(details, indent=4)
            return formatted_details
        except (json.JSONDecodeError, IndexError):
            return "Detalhes não encontrados."

    def stop_containers(self):
        try:
            running_ids = subprocess.check_output(["docker", "ps", "-q"]).decode().split()
            if running_ids:
                subprocess.run(["docker", "stop"] + running_ids)
                log_and_notify("Containers parados automaticamente.")
            else:
                log_and_notify("Nenhum container em execução.")
        except Exception as e:
            log_and_notify(f"Erro ao parar containers: {str(e)}")

    def start_container_by_name_or_id(self, name_or_id):
        try:
            self.client_docker.containers.get(name_or_id).start()
        except Exception as e:
            print("Erro", f"Erro ao iniciar container:\n{str(e)}")

    def stop_container_by_name_or_id(self, name_or_id):
        try:
            self.client_docker.containers.get(name_or_id).stop()
        except Exception as e:
            print("Erro", f"Erro ao parar container:\n{str(e)}")

    def remove_container_by_name_or_id(self, name_or_id):
        try:
            self.client_docker.containers.get(name_or_id).remove(force=True)
        except Exception as e:
            print("Erro", f"Erro ao remover container:\n{str(e)}")

    def pull_image(self, image_name):
        try:
            self.client_docker.images.pull(image_name)
        except Exception as e:
            # Fecha a janela de progresso após a conclusão
            print("Erro", f"Erro ao baixar imagem:\n{str(e)}")

    def pull_image_with_progress(self, image_name):
        response = self.api_client.pull(image_name, stream=True, decode=True)
        for line in response:
            yield line  # linha com progresso, status, id, etc.

    def remove_image(self, image_name):
        try:
            self.client_docker.images.remove(image=image_name)
        except Exception as e:
            print("Erro", f"Erro ao remover imagem:\n{str(e)}")

    def get_available_networks(self):
        try:
            networks = self.client_docker.networks.list()
            network_names = [network.name for network in networks]
            return network_names
        except Exception as e:
            print("Erro", f"Erro ao listar redes:\n{str(e)}")

    def build_container(self, image_selected, container_name, port, network, env_vars):
        try:
            # container_name = self.container_name_entry.get()
            # port = self.port_entry.get()
            # network = self.network_combobox.get()
            environment = dict(env_vars)

            self.client_docker.containers.run(image_selected, name=container_name,
                                              ports={port.split(':')[1]: port.split(':')[0]}, network=network,
                                              environment=environment,
                                              detach=True)
        except Exception as e:
            print("Erro", f"Erro ao criar container:\n{str(e)}")