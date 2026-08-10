output "labday_public_ips" {
  description = "Public IPs of all EC2 instances"
  value       = aws_instance.labday[*].public_ip
}

output "labday_public_dns" {
  description = "Public DNS of all EC2 instances"
  value       = aws_instance.labday[*].public_dns
}

output "labday_private_ips" {
  description = "Private IPs of all EC2 instances"
  value       = aws_instance.labday[*].private_ip
}

output "registrationform_public_ips" {
  description = "Public IPs of registration form"
  value       = aws_instance.registration_form.public_ip
}

