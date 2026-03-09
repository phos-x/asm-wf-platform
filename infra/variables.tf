variable "project_name" {
  description = "Project name prefix"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

variable "allowed_cidr" {
  description = "CIDR allowed to access asm (and optional SSH)"
  type        = string
}

variable "enable_ssh" {
  description = "Enable SSH ingress on port 22"
  type        = bool
  default     = false
}

variable "ec2_instance_type" {
  description = "EC2 instance type for MLflow"
  type        = string
  default     = "t3.micro"
}

variable "ec2_ami_id" {
  description = "AMI ID for EC2 (e.g., Ubuntu LTS)"
  type        = string
}

variable "artifact_bucket_arn" {
  description = "S3 bucket ARN for artifacts (can be dummy/placeholder initially)"
  type        = string
  default     = "arn:aws:s3:::dummy-artifact-bucket"
}

variable "asm_repo_url" {
  description = "Git repo URL containing docker-compose asm setup"
  type        = string
}

#------------------------




