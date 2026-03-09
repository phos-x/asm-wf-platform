terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

resource "aws_instance" "asm_ec2" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.asm_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.asm_instance_profile.name

  associate_public_ip_address = true

  user_data = templatefile("${path.module}/user_data/mlflow_bootstrap.sh", {
    asm_repo_url = var.asm_repo_url
  })

  tags = {
    Name = "${var.project_name}-asm-ec2"
  }
}



