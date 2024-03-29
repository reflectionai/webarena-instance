from flask import Flask
import os

app = Flask(__name__)


@app.route('/reset', methods=['POST'])
def reset_containers():
    # Define your containers and their snapshot images
    containers = {
        'gitlab': 'snapshot-gitlab:initial',
        'shopping': 'snapshot-shopping:initial',
        'shopping_admin': 'snapshot-shopping_admin:initial',
        'forum': 'snapshot-forum:initial',
    }

    for container, image in containers.items():
        os.system(f"docker stop {container}")
        os.system(f"docker rm {container}")
        os.system(f"docker run -d --name {container} {image}")

    return "Containers reset to initial state", 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
