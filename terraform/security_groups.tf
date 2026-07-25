# =============================================================================
# セキュリティグループ
# =============================================================================

# Lambda 用
resource "aws_security_group" "lambda" {
  name_prefix = "${var.project_name}-lambda-"
  description = "Security group for Lambda function"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound (NAT Instance, RDS)"
  }

  tags = { Name = "${var.project_name}-lambda-sg" }
}

# NAT Instance 用
resource "aws_security_group" "nat_instance" {
  name_prefix = "${var.project_name}-nat-"
  description = "Security group for NAT Instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["10.0.10.0/24", "10.0.11.0/24"]
    description = "All traffic from private subnets"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = { Name = "${var.project_name}-nat-sg" }
}

# EFS 用（SQLite ストレージ）— Lambda からの NFS(2049) のみ許可
resource "aws_security_group" "efs" {
  name_prefix = "${var.project_name}-efs-"
  description = "Security group for EFS (SQLite storage)"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
    description     = "NFS from Lambda only"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-efs-sg" }
}
