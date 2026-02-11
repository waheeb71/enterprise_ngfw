# 🌐 Deploying Enterprise NGFW on a Virtual Machine (VM)

This guide walks you through deploying the project on a Linux VM (e.g., Ubuntu 20.04/22.04) on any cloud provider (AWS, Azure, DigitalOcean) or local hypervisor (VirtualBox, VMware).

## 1. Prepare the VM

### Update System
Connect to your VM via SSH and update the package list:
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Docker & Docker Compose
The easiest way to install Docker on Linux:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Add your user to the docker group (so you don't need `sudo` for every command):
```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verify installation:
```bash
docker --version
docker compose version
```

## 2. Transfer Project Files

You have two options to get the code onto the VM:

### Option A: Git Clone (Recommended)
If your project is on GitHub/GitLab:
```bash
git clone https://github.com/your-username/enterprise-ngfw.git
cd enterprise-ngfw
```

### Option B: SCP / SFTP (Manual)
Copy the project folder from your local machine to the VM:
```bash
# Run this on your local machine
scp -r /path/to/enterprise_ngfw user@vm-ip-address:/home/user/
```

## 3. Configuration

1.  Navigate to the project directory:
    ```bash
    cd enterprise_ngfw
    ```

2.  Create the production environment file:
    ```bash
    cp .env.example .env
    ```

3.  Edit the `.env` file:
    ```bash
    nano .env
    ```
    - **Crucial:** Change `NGFW_SECRET_KEY` to a random secure string.
    - Set `NGFW_ENV=production`.
    - Save and exit (Ctrl+O, Enter, Ctrl+X).

## 4. Run the Application

Start the services in the background using Docker Compose:

```bash
docker compose up -d --build
```

- `--build`: Forces rebuilding the images to ensure you have the latest code.
- `-d`: Detached mode (runs in background).

## 5. Verify Deployment

### Check Status
```bash
docker compose ps
```
You should see `ngfw-api` and `ngfw-dashboard` with status `Up`.

### View Logs
```bash
docker compose logs -f
```
(Press `Ctrl+C` to exit logs)

### Access the Application
Open your browser and navigate to:
- **Dashboard:** `http://<VM-IP-ADDRESS>:8080`
- **API Docs:** `http://<VM-IP-ADDRESS>:8000/docs`

> **Note:** Ensure your VM's firewall (Security Group) allows inbound traffic on ports `8000` and `8080`.

## 6. Maintenance

### Update Application
```bash
git pull
docker compose up -d --build
```

### Stop Application
```bash
docker compose down
```
