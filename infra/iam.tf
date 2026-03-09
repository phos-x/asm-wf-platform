data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "asm_ec2_role" {
  name               = "${var.project_name}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

# Attach AWS managed SSM policy for SSH-less access
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.asm_ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Minimal S3 access for future artifact offload (optional)
data "aws_iam_policy_document" "s3_minimal" {
  statement {
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket"
    ]
    resources = [
      var.artifact_bucket_arn,
      "${var.artifact_bucket_arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3_minimal_policy" {
  name   = "${var.project_name}-s3-minimal"
  policy = data.aws_iam_policy_document.s3_minimal.json
}

resource "aws_iam_role_policy_attachment" "s3_minimal_attach" {
  role       = aws_iam_role.asm_ec2_role.name
  policy_arn = aws_iam_policy.s3_minimal_policy.arn
}

resource "aws_iam_instance_profile" "asm_instance_profile" {
  name = "${var.project_name}-instance-profile"
  role = aws_iam_role.asm_ec2_role.name
}
