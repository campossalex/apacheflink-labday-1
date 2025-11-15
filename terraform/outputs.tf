output "instance_public_ips" {
  description = "Public IPs of all EC2 instances"
  value       = aws_instance.labday[*].public_ip
}

output "instance_public_dns" {
  description = "Public DNS of all EC2 instances"
  value       = aws_instance.labday[*].public_dns
}

output "instance_private_ips" {
  description = "Private IPs of all EC2 instances"
  value       = aws_instance.labday[*].private_ip
}

