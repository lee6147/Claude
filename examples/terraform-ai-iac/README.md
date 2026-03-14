# Terraform + AI IaC 실전 예제

> AI 코딩 도구로 클라우드 인프라를 코드로 관리하는 실전 가이드 — IaC 자동 생성부터 드리프트 감지까지

## 이 예제에서 배울 수 있는 것

- AI로 Terraform 코드를 빠르게 생성하고 검증하는 워크플로우
- CLAUDE.md로 인프라 컨텍스트를 정확하게 전달하는 패턴
- `terraform plan` 결과를 AI가 분석해서 위험 요소를 잡아내는 방법
- 드리프트 감지를 자동화하는 CI/CD 파이프라인 구성

## 프로젝트 구조

```
terraform-ai-iac/
├── CLAUDE.md              # AI 도구 프로젝트 설정
├── environments/
│   ├── dev/
│   │   ├── main.tf        # Dev 환경 진입점
│   │   ├── variables.tf   # 환경별 변수
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── terraform.tfvars
├── modules/
│   ├── networking/
│   │   ├── main.tf        # VPC, Subnet, Security Group
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── compute/
│   │   ├── main.tf        # EC2, Auto Scaling
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── database/
│       ├── main.tf        # RDS, ElastiCache
│       ├── variables.tf
│       └── outputs.tf
├── scripts/
│   ├── drift-check.sh     # 드리프트 감지 스크립트
│   └── plan-review.sh     # Plan 결과 AI 분석
├── .github/
│   └── workflows/
│       └── terraform-ci.yml
└── README.md
```

## 시작하기

### Step 1: CLAUDE.md 작성

인프라 프로젝트에서 AI 도구를 쓸 때 가장 중요한 건 **컨텍스트 전달**이에요. `CLAUDE.md`로 프로젝트 구조와 규칙을 명시해요.

```markdown
# CLAUDE.md

## Project
terraform-ai-iac — AWS 인프라를 Terraform으로 관리하는 프로젝트

## Architecture
- AWS 리전: ap-northeast-2 (서울)
- 환경: dev / prod (environments/ 하위)
- 모듈 구조: modules/{networking,compute,database}

## Rules
- 모든 리소스에 `Environment`, `ManagedBy` 태그 필수
- Security Group은 최소 권한 원칙 (0.0.0.0/0 인바운드 금지)
- RDS는 반드시 private subnet에 배치
- State는 S3 + DynamoDB 원격 백엔드 사용
```

### Step 2: 네트워킹 모듈 생성

AI에게 모듈 생성을 요청할 때 구체적인 요구사항을 전달하면 정확도가 올라가요.

```bash
# Claude Code 프롬프트 예시
claude "modules/networking에 VPC 모듈을 만들어줘.
- CIDR: 10.0.0.0/16
- Public subnet 2개, Private subnet 2개
- NAT Gateway 1개 (비용 절약)
- 모든 리소스에 Name 태그 포함"
```

생성되는 코드 예시:

```hcl
# modules/networking/main.tf

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "${var.project}-vpc"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_subnet" "public" {
  count             = length(var.public_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidrs[count.index]
  availability_zone = var.azs[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name        = "${var.project}-public-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.azs[count.index]

  tags = {
    Name        = "${var.project}-private-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name        = "${var.project}-nat"
    Environment = var.environment
  }
}
```

### Step 3: Plan 결과 AI 분석

`terraform plan`의 출력을 AI에게 넘겨서 위험 요소를 검토할 수 있어요.

```bash
#!/bin/bash
# scripts/plan-review.sh

cd environments/dev
terraform plan -no-color -out=plan.tfplan 2>&1 | tee plan-output.txt

# Plan 결과를 AI로 분석
claude "plan-output.txt를 분석해줘.
체크 항목:
1. destroy되는 리소스가 있는지
2. Security Group 변경이 있는지
3. 비용에 영향을 주는 변경이 있는지
4. 다운타임이 발생할 수 있는 변경이 있는지
위험도를 상/중/하로 분류하고, 각 항목에 대해 설명해줘."
```

## 핵심 코드

### 드리프트 감지 스크립트

수동 콘솔 변경을 자동으로 잡아내는 스크립트예요. CI/CD에 연결하면 정기적으로 체크할 수 있어요.

```bash
#!/bin/bash
# scripts/drift-check.sh

set -euo pipefail

ENVIRONMENTS=("dev" "prod")
DRIFT_FOUND=0

for ENV in "${ENVIRONMENTS[@]}"; do
  echo "🔍 ${ENV} 환경 드리프트 체크..."
  cd "environments/${ENV}"

  terraform init -backend=true -input=false > /dev/null 2>&1

  # refresh로 실제 상태와 비교
  PLAN_OUTPUT=$(terraform plan -detailed-exitcode -no-color 2>&1) || EXIT_CODE=$?

  if [ "${EXIT_CODE:-0}" -eq 2 ]; then
    echo "⚠️ ${ENV}에서 드리프트 감지!"
    echo "$PLAN_OUTPUT" > "drift-report-${ENV}.txt"
    DRIFT_FOUND=1
  else
    echo "✅ ${ENV} — 드리프트 없음"
  fi

  cd ../..
done

if [ $DRIFT_FOUND -eq 1 ]; then
  echo "🚨 드리프트가 감지되었어요. drift-report-*.txt를 확인하세요."
  exit 1
fi
```

**왜 이렇게 했나요?**

`terraform plan -detailed-exitcode`는 변경사항이 있으면 exit code 2를 반환해요. 이걸 이용하면 스크립트에서 드리프트 유무를 정확하게 판단할 수 있어요.

### GitHub Actions CI/CD

```yaml
# .github/workflows/terraform-ci.yml

name: Terraform CI

on:
  pull_request:
    paths: ['environments/**', 'modules/**']
  schedule:
    - cron: '0 9 * * 1'  # 매주 월요일 드리프트 체크

jobs:
  validate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        environment: [dev, prod]
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.x

      - name: Terraform Init
        working-directory: environments/${{ matrix.environment }}
        run: terraform init -backend=false

      - name: Terraform Validate
        working-directory: environments/${{ matrix.environment }}
        run: terraform validate

      - name: Terraform Format Check
        run: terraform fmt -check -recursive

  plan:
    needs: validate
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3

      - name: Terraform Plan
        working-directory: environments/dev
        run: |
          terraform init
          terraform plan -no-color -out=plan.tfplan | tee plan-output.txt

      - name: PR에 Plan 결과 코멘트
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('environments/dev/plan-output.txt', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## Terraform Plan 결과\n\`\`\`\n${plan.slice(0, 60000)}\n\`\`\``
            });

  drift-check:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: hashicorp/setup-terraform@v3

      - name: 드리프트 체크
        run: bash scripts/drift-check.sh
        continue-on-error: true

      - name: 드리프트 알림
        if: failure()
        run: |
          echo "드리프트가 감지되었습니다. 리포트를 확인하세요."
```

## AI 활용 포인트

| 상황 | 프롬프트 예시 |
|------|-------------|
| 새 모듈 생성 | `"RDS PostgreSQL 모듈을 만들어줘. Multi-AZ, 암호화 활성화, private subnet 배치"` |
| 보안 검토 | `"이 Security Group 규칙을 검토해줘. 과도하게 열린 포트가 있는지 확인"` |
| 비용 최적화 | `"이 인프라의 예상 월 비용을 분석해줘. 절약할 수 있는 부분을 제안"` |
| 드리프트 분석 | `"drift-report-prod.txt를 분석해줘. 누가 왜 변경했는지 추정하고 해결 방안을 제안"` |
| 모듈 리팩토링 | `"compute 모듈을 for_each 패턴으로 리팩토링해줘. 환경별 인스턴스 수를 다르게 설정"` |
| 변수 정리 | `"variables.tf에서 사용하지 않는 변수를 찾아줘"` |

## 자주 쓰는 패턴

### 원격 State 설정

```hcl
# environments/dev/backend.tf

terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "ap-northeast-2"
    dynamodb_table = "terraform-lock"
    encrypt        = true
  }
}
```

### 모듈 호출

```hcl
# environments/dev/main.tf

module "networking" {
  source = "../../modules/networking"

  project              = var.project
  environment          = "dev"
  vpc_cidr             = "10.0.0.0/16"
  public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnet_cidrs = ["10.0.10.0/24", "10.0.20.0/24"]
  azs                  = ["ap-northeast-2a", "ap-northeast-2c"]
}

module "compute" {
  source = "../../modules/compute"

  project       = var.project
  environment   = "dev"
  vpc_id        = module.networking.vpc_id
  subnet_ids    = module.networking.private_subnet_ids
  instance_type = "t3.medium"
  min_size      = 1
  max_size      = 3
}
```

### 태그 표준화

```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Team        = "platform"
  }
}
```

## 주의할 점

| 항목 | 설명 |
|------|------|
| State 파일 보안 | `.tfstate`에 민감 정보가 포함될 수 있어요. 반드시 암호화된 원격 백엔드를 쓰세요 |
| Plan 없이 Apply 금지 | AI가 생성한 코드도 반드시 `plan` → 검토 → `apply` 순서를 지켜요 |
| 모듈 버전 고정 | 외부 모듈은 `version` 속성으로 버전을 고정하세요 |
| Secret 관리 | API 키, DB 패스워드는 `terraform.tfvars`에 넣지 말고 AWS Secrets Manager를 사용하세요 |

---

**더 자세한 가이드:** [claude-code/playbooks](../../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
