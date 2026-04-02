# Claude Lean

코딩 에이전트 세션의 정확한 토큰 측정, 비용 분석, 자동 최적화, 벤치마킹 도구

## 작동 원리

Claude Code의 매 턴마다 시스템 프롬프트, CLAUDE.md, MEMORY.md, MCP 스키마, 스킬 메타데이터가 다시 로드됩니다. 비대한 설정은 매 메시지마다 조용히 토큰과 비용을 소모합니다.

Claude Lean은 **tiktoken 기반 카운팅**으로 각 구성 요소의 정확한 비용을 측정한 후, 최적화를 도와줍니다. 부정확한 "bytes / 4" 추정이 아닌 실측입니다.

세션 시작 시 자동으로 설정을 확인하고, 무거운 부분이 있으면 경고합니다. `/diagnose`로 전체 분석, `/optimize`로 자동 최적화, `/benchmark`로 전후 비교를 실행할 수 있습니다.

## 설치

**참고:** 플랫폼별로 설치 방법이 다릅니다.

### Claude Code (공식 마켓플레이스)

```bash
/plugin install claude-lean@claude-plugins-official
```

### Claude Code (플러그인 마켓플레이스)

마켓플레이스를 먼저 등록:

```bash
/plugin marketplace add taejunoh/claude-lean
```

설치:

```bash
/plugin install claude-lean@claude-lean-marketplace
```

### Cursor

Cursor Agent 챗에서:

```text
/add-plugin claude-lean
```

### Codex

Codex에게 말하세요:

```
Fetch and follow instructions from https://raw.githubusercontent.com/taejunoh/claude-lean/refs/heads/main/.codex/INSTALL.md
```

### OpenCode

OpenCode에게 말하세요:

```
Fetch and follow instructions from https://raw.githubusercontent.com/taejunoh/claude-lean/refs/heads/main/.opencode/INSTALL.md
```

### Gemini CLI

```bash
gemini extensions install https://github.com/taejunoh/claude-lean
```

### 설치 확인

새 세션을 시작하고 `/diagnose`를 실행하세요. 구성 요소별 토큰 분석 테이블이 표시되면 성공입니다.

## 커맨드

| 커맨드 | 기능 |
|--------|------|
| `/diagnose` | 모든 설정 파일 스캔, 토큰 측정, 비용 추정 |
| `/optimize [경로]` | CLAUDE.md 섹션 분류 후 무거운 콘텐츠를 refs/로 분리 |
| `/benchmark [이전] [이후]` | 최적화 전후 토큰 수와 비용 절감 비교 |

## 워크플로우

1. **진단** — `/diagnose`로 토큰이 어디에 쓰이는지 확인. 각 구성 요소에 GREEN/YELLOW/RED 등급 부여.

2. **최적화** — CLAUDE.md가 YELLOW이나 RED이면 `/optimize` 실행. 섹션별로 필수(유지), 이동 가능(refs/로 분리), 제거 가능(아카이브)으로 분류. 항상 백업 생성.

3. **벤치마크** — `/benchmark`로 전후 비교. tiktoken 측정 토큰 수, 모델별 비용 절감, naive 추정 대비 정확도 차이를 확인.

## 구성 요소

### 스킬
- **claude-lean** — Python 스크립트 5개를 포함한 진단/최적화 스킬

### 커맨드
- **diagnose** — 빠른 토큰 스캔과 비용 추정
- **optimize** — CLAUDE.md 분석 및 자동 최적화
- **benchmark** — 검증된 데이터로 전후 비교

### 훅
- **SessionStart** — 시작 시 CLAUDE.md 크기와 MCP 수를 확인, 과중하면 경고

### 스크립트

| 스크립트 | 용도 |
|----------|------|
| `count_tokens.py` | tiktoken 기반 토큰 카운터 (언어별 폴백 포함) |
| `analyze_cost.py` | 캐시 시나리오 포함 모델별 비용 추정 |
| `optimize_claude_md.py` | 섹션 분류기 및 자동 최적화기 |
| `benchmark.py` | 전후 비교 벤치마크 러너 |
| `generate_report.py` | 종합 마크다운 리포트 생성기 |

## 왜 bytes/4 대신 tiktoken인가?

"bytes / 4" 방식은 한국어, 일본어, 이모지 등 비ASCII 텍스트에서 40-80% 오차가 발생합니다. tiktoken의 `cl100k_base` 인코딩은 Claude의 토크나이저와 유사하며 5-15% 이내의 정확도를 보입니다. 벤치마크 커맨드가 두 측정값을 나란히 보여주므로 차이를 직접 확인할 수 있습니다.

## 테스트 실행

```bash
cd skills/claude-lean/scripts
pip install tiktoken pytest
python -m pytest tests/test_all.py -v
```

28개 테스트 케이스 포함.

## 업데이트

```bash
/plugin update claude-lean
```

## 라이선스

MIT
