# =============================================================================
# EFS — SQLite の永続化ストレージ（RDS の代替）
#
# データ量が小さく実質単一ユーザーのため、RDS(MySQL) ではなく EFS 上の SQLite を
# 使う（money-pilot と同方式）。常時稼働課金がなく大幅に安価。
# DB ファイルは access point ルート(/lambda)直下 = Lambda から /mnt/efs/db.sqlite3。
# =============================================================================

resource "aws_efs_file_system" "main" {
  encrypted = true

  tags = { Name = "${var.project_name}-efs" }
}

# マウントターゲット（各プライベートサブネット）
resource "aws_efs_mount_target" "private_a" {
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = aws_subnet.private_a.id
  security_groups = [aws_security_group.efs.id]
}

resource "aws_efs_mount_target" "private_c" {
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = aws_subnet.private_c.id
  security_groups = [aws_security_group.efs.id]
}

# Lambda 用アクセスポイント（posix user 1000/1000、ルート /lambda）
resource "aws_efs_access_point" "lambda" {
  file_system_id = aws_efs_file_system.main.id

  root_directory {
    path = "/lambda"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  posix_user {
    gid = 1000
    uid = 1000
  }

  tags = { Name = "${var.project_name}-efs-ap" }
}
