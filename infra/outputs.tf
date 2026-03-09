output "mlflow_ec2_public_ip" {
  description = "Public IP of the MLflow EC2 instance"
  value       = aws_instance.mlflow_ec2.public_ip
}

output "mlflow_ec2_public_dns" {
  description = "Public DNS of the MLflow EC2 instance"
  value       = aws_instance.mlflow_ec2.public_dns
}
