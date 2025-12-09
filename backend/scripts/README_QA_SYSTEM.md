# Quality Assurance System

Complete QA system implementation as per `docs/28-QUALITY-ASSURANCE-SYSTEM.md`.

## Components

### Backend Services

1. **QualityScorer** (`services/quality_scorer_service.py`)
   - Comprehensive quality scoring (face, technical, realism)
   - Automatic pass/fail determination
   - Auto-approval for high-quality content

2. **DetectionTester** (`services/detection_tester_service.py`)
   - AI detection testing using multiple tools
   - HiveModeration, SensityAI, AIOrNot integration
   - Pass/fail determination based on thresholds

3. **QualityMetrics** (`services/quality_metrics_service.py`)
   - KPI tracking and statistics
   - Generation, quality, detection, and efficiency metrics

4. **QualityDashboard** (`services/quality_dashboard_service.py`)
   - Dashboard data aggregation
   - Trend analysis
   - Alert generation

5. **QualityImprover** (`services/quality_improver_service.py`)
   - Rejection pattern analysis
   - Improvement recommendations
   - Continuous improvement tracking

### Database Models

- `QualityScore`: Stores quality scores for media items
- `QualityReview`: Manual review records
- `RejectionLog`: Rejection tracking and analysis
- `DetectionTest`: AI detection test results

### API Endpoints

- `POST /api/qa/score` - Score content quality
- `POST /api/qa/detection-test` - Test AI detection
- `GET /api/qa/metrics` - Get quality metrics
- `GET /api/qa/dashboard` - Get dashboard data
- `GET /api/qa/improvements` - Get improvement analysis
- `POST /api/qa/review` - Create manual review
- `POST /api/qa/reject` - Log rejection
- `POST /api/qa/batch-test` - Batch quality testing

### Web Components

- `QualityDashboard` - Main dashboard component
- `QualityReviewInterface` - Manual review interface
- QA Dashboard page at `/qa-dashboard`

### Testing Scripts

- `scripts/test_quality_batch.py` - Batch quality testing script

## Usage

### Automatic QA in Generation Pipeline

QA is automatically integrated into the generation pipeline. When content is generated:

1. Quality is scored using `QualityScorer`
2. AI detection is tested using `DetectionTester`
3. Results are saved to database
4. Content is auto-rejected if below thresholds

### Manual Quality Review

Use the review interface to manually review content:

```typescript
import { QualityReviewInterface } from '@/components/quality/QualityReviewInterface'

<QualityReviewInterface 
  mediaId={mediaId}
  onReviewComplete={() => console.log('Review complete')}
/>
```

### Batch Testing

Test quality for multiple files:

```bash
python backend/scripts/test_quality_batch.py /path/to/content --output results.json
```

### Dashboard

View quality metrics and trends:

Navigate to `/qa-dashboard` in the web application.

## Configuration

### Quality Thresholds

- Minimum overall score: 8.0/10
- Minimum face score: 8.0/10
- Minimum technical score: 7.5/10
- Minimum realism score: 8.0/10
- Auto-approval: 9.0/10 overall, 8.5/10 all categories

### Detection Thresholds

- Pass criteria: Average < 0.3 (30%)
- Individual tools: < 0.4 (40%)
- No tool: > 0.5 (50%)

## Integration

The QA system is automatically integrated into:

1. **Generation Service**: Quality scoring and detection testing after generation
2. **Media Service**: Quality scores stored with media items
3. **Web Application**: Dashboard and review interfaces

## Next Steps

1. Configure API keys for detection tools (Hive, Sensity, AIOrNot)
2. Set up monitoring and alerting
3. Review and adjust thresholds based on results
4. Implement continuous improvement workflows
