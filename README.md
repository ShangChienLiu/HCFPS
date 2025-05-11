# Hybrid Cloud File Processing System

A unified, cross-cloud file processing platform that automates the conversion, compression, and management of scientific, video, and robotics data across AWS and Google Cloud Platform (GCP). This system leverages Terraform for infrastructure-as-code, Docker for containerized processing, and a Flask-based Web UI for user interaction and task management.

---

## Repository Structure

```
.
├── docker/        # Docker images, compose files, and processing scripts
├── terraform/     # Terraform IaC for AWS and GCP infrastructure
├── webui/         # Web UI and API server (Flask app)
├── config/        # Configuration files (gitignored)
├── logs/          # Log files (gitignored)
├── note/          # Project notes and documentation (gitignored)
├── data-examples/ # Example data files (gitignored)
```

### Folder Overviews

- **docker/**: Contains Dockerfiles, docker-compose files, and Python scripts for file processing (conversion, compression, renaming). Includes subfolders for keys and logs (both gitignored).
- **terraform/**: All Terraform code for provisioning and managing AWS and GCP resources. Includes cloud-specific subfolders and state/variable files. Automates compute, storage, networking, and security setup.
- **webui/**: Flask-based web application and API server for submitting, monitoring, and managing processing tasks. Contains static assets, templates, utility scripts, and a Python virtual environment (gitignored).

---

## Features

- **Hybrid Cloud Processing**: Seamlessly process files on AWS or GCP, with cross-cloud output support.
- **Supported Formats**: Video (MP4, MOV, AVI, MKV, WEBM), Robotics (ROS bags, MCAP), Scientific (HDF5), Text/Data (TXT, CSV, JSON, XML, YAML).
- **Processing Actions**: Video conversion (H.265), compression (ZIP), renaming, and more.
- **Scalable Infrastructure**: Auto-scaling compute resources on both clouds, managed via Terraform.
- **Web UI & API**: User-friendly interface for task submission and monitoring.
- **Secure Credential Handling**: Uses secret managers and .gitignore to protect sensitive data.

---

## Quick Start

### Prerequisites
- AWS CLI configured
- Google Cloud SDK installed
- Terraform 1.0+
- Docker
- Python 3.8+

### Setup Steps
1. **Clone the repository**
2. **Configure cloud credentials** (see Security section)
3. **Customize `terraform/terraform.tfvars`** for your environment
4. **Deploy infrastructure**:
   ```
   cd terraform
   terraform init
   terraform apply
   ```
5. **Build and run Docker containers** (for local processing):
   ```
   cd docker
   docker-compose up --build
   ```
6. **Start the Web UI**:
   ```
   cd webui
   pip install -r requirements.txt
   python app.py
   ```

---

## Usage

- **Submit tasks** via the Web UI or directly to AWS SQS / GCP Pub/Sub (see API docs in `webui/`)
- **Monitor processing** through the Web UI or cloud dashboards (CloudWatch, Cloud Logging)
- **Processed files** are stored in your configured S3 or GCS buckets

---

## Security & Sensitive Information

- All sensitive files (keys, credentials, logs, configs, notes, data-examples) are gitignored by default.
- Use cloud secret managers for runtime credentials.
- Never commit `.env`, `*key.json`, `*credentials*.json`, or any private key files.
- Review and update `.gitignore` as needed for your workflow.

---

## Customization

- Add new processing actions by extending scripts in `docker/processor/` and updating the Web UI/API.
- Adjust auto-scaling and resource parameters in `terraform/variables.tf`.
- Modify UI/UX in `webui/templates/` and static assets.

---

## Troubleshooting

- **Infrastructure issues**: Check Terraform logs and cloud provider dashboards.
- **Processing errors**: Review logs in `logs/` or cloud logging services.
- **Web UI/API issues**: Check Flask logs and ensure all dependencies are installed.

---

## License

This project is provided for educational and research purposes. Please review and comply with the licenses of all dependencies and cloud services used.
