provider "google" {
  project = var.project_id
  region  = "us-central1"
}

variable "project_id" {}
variable "zone" {
  default = "us-central1-a"
}

# Create a VPC network (optional, or use default)
resource "google_compute_network" "vpc_network" {
  name                    = "voice-agent-network"
  auto_create_subnetworks = true
}

# Firewall to allow HTTP/HTTPS
resource "google_compute_firewall" "http" {
  name    = "allow-http-https"
  network = google_compute_network.vpc_network.name
  allow {
    protocol = "tcp"
    ports    = ["80","443","8000"]
  }
}

# Compute instance
resource "google_compute_instance" "voice_agent_vm" {
  name         = "voice-agent-vm"
  machine_type = "f1-micro"        # free tier eligible
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 10
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = google_compute_network.vpc_network.name
    access_config {}
  }

  metadata = {
    # Startup script to install Docker and run container
    startup-script = <<-EOF
      #!/bin/bash
      apt-get update
      apt-get install -y docker.io python3-pip
      # Optionally install git, etc.
      # Authenticate to Google for cloud storage
      gcloud auth activate-service-account --key-file=/etc/gcp-key.json
      # Pull Docker image from Container Registry (if we push it)
      docker run -d -p 8000:8000 -e OPENAI_API_KEY=${OPENAI_API_KEY} -e TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID} -e TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN} gcr.io/${var.project_id}/voice-ai-agent:latest
    EOF
  }

  # Attach a service account with Storage admin
  service_account {
    email  = google_service_account.vm_sa.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}

# Create a service account for the VM
resource "google_service_account" "vm_sa" {
  account_id   = "voice-agent-vm-sa"
  display_name = "Voice Agent VM Service Account"
}

# Storage bucket for transcripts
resource "google_storage_bucket" "transcripts" {
  name     = "${var.project_id}-voice-transcripts"
  location = "US"
  force_destroy = true
}
