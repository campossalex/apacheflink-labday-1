# Security group to allow SSH access
resource "aws_security_group" "allow_ssh" {
  name        = "allow_ssh"
  description = "Allow SSH from anywhere"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8085
    to_port     = 8085
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 4200
    to_port     = 4200
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 instances
resource "aws_instance" "labday" {
  count         = var.instance_count
  ami           = var.instance_ami
  instance_type = var.instance_type
  key_name      = var.key_name
  vpc_security_group_ids = [aws_security_group.allow_ssh.id]

  root_block_device {
    volume_size = 40          # GB
    volume_type = "gp3"       # General-purpose SSD (recommended)
    delete_on_termination = true
  }

  # Run as root using user_data
  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    # Install git
    yum update -y
    yum install -y git

    # Clone your repo
    cd /root
    git clone ${var.git_repo} ververica-platform-playground

    # Run pre-install script
    sudo ./ververica-platform-playground/pre-install.sh > /var/log/labday_setup.log 2>&1

    # Run setup script
    sudo ./ververica-platform-playground/setup.sh > /var/log/labday_setup.log 2>&1

    # Run post-install script   
    sudo ./ververica-platform-playground/post-install.sh > /var/log/labday_setup.log 2>&1

    # Run response-install script   
    sudo ./ververica-platform-playground/response-install.sh > /var/log/labday_setup.log 2>&1

  EOF

  tags = {
    Name = "labday-instance-${count.index}"
  }
}

