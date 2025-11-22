variable "aws_region" { default = "us-east-1" }
variable "instance_type" { default = "t3.micro" }
variable "ami_id" { default = "ami-0a91cd140a1fc148a" } # example Ubuntu; check for your region
variable "public_key_path" { default = "~/.ssh/id_rsa.pub" }
variable "my_ip_cidr" { default = "0.0.0.0/0" } # replace with "your_ip/32" for SSH security

