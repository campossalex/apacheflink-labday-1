provider "aws" {
  region = "eu-central-1"
}
  
# Number of EC2 instances
variable "instance_count" {
  default = 1
}

# EC2 instance AMI
variable "instance_ami" {
  default = "ami-07801e143d22c782d"
}

# EC2 instance type
variable "instance_type" {
  default = "c6a.2xlarge"
}
  
# Your EC2 key pair name (must already exist in AWS)
variable "key_name" {
  default = "acampos-frankfurt-key"
}
  
# Your Git repo and script name
variable "git_repo" {   
  default = "https://github.com/campossalex/apacheflink-labday-1.git"
}

# Owner tag
variable "owner" {
}

