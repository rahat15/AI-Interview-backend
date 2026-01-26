# Resume Upload API - Comprehensive Response

## Endpoint

```
POST /v1/resume/upload
```

## Request

```bash
curl -X POST "http://localhost:8000/v1/resume/upload" \
  -F "file=@john_doe_resume.pdf" \
  -F "user_id=user123" \
  -F "jd_text=We are looking for a senior developer with React and Node.js experience..."
```

## Response Format

```json
{
  "message": "Resume uploaded successfully",
  "resume": {
    "id": "65f1a2b3c4d5e6f7g8h9i0j1",
    "filename": "john_doe_resume.pdf",
    "url": "http://localhost:3000/uploads/users/user123/1710123456789-john_doe_resume.pdf",
    "stats": {
      "overall_score": 8.2,
      "sections": {
        "structure": {
          "score": 9.0,
          "feedback": "Clear sections, Good formatting"
        },
        "content_quality": {
          "score": 8.5,
          "feedback": "Strong content, Relevant experience"
        },
        "professional_presentation": {
          "score": 8.0,
          "feedback": "Professional tone, Well organized"
        }
      },
      "strengths": [
        "Strong technical background in React and Node.js",
        "Quantifiable achievements in previous roles",
        "Clear and professional formatting",
        "Relevant certifications included"
      ],
      "weaknesses": [
        "Could include more soft skills",
        "Missing portfolio links",
        "Some experience descriptions could be more detailed"
      ],
      "recommendations": [
        "Add quantifiable achievements",
        "Include relevant keywords",
        "Optimize for ATS compatibility"
      ],
      "ats_compatibility": {
        "score": 8.5,
        "issues": [
          "Use standard section headings",
          "Avoid complex formatting"
        ]
      },
      "keyword_analysis": {
        "matched_keywords": [],
        "missing_keywords": [],
        "keyword_density": 0.12
      }
    },
    "improvement_resume": {
      "fit_score": 85.5,
      "matching_skills": [],
      "missing_skills": [],
      "suggestions": [],
      "rewritten_sections": {
        "improved_resume": "...",
        "cover_letter": "...",
        "benchmark": "..."
      },
      "overall_improvement_score": 92.3,
      "recommendations": [
        "Highlight leadership experience",
        "Add specific project examples",
        "Include relevant certifications",
        "Optimize for ATS"
      ]
    }
  },
  "cv_quality": {
    "overall_score": 85,
    "band": "Good",
    "subscores": [
      {
        "dimension": "Structure",
        "score": 4.2,
        "max_score": 5,
        "evidence": [
          "Clear sections",
          "Good formatting"
        ]
      }
    ]
  },
  "jd_match": {},
  "fit_index": {}
}
```

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file` | File | Yes | Resume file (PDF, DOCX, DOC, TXT) |
| `user_id` | String | No | User identifier (default: "default") |
| `jd_text` | String | No | Job description for matching analysis |

## Response Fields

### Main Response
- `message`: Success message
- `resume`: Resume data and analysis
- `cv_quality`: Detailed CV quality scores
- `jd_match`: Job description matching scores (if JD provided)
- `fit_index`: Overall fit index (if JD provided)

### Resume Object
- `id`: MongoDB document ID
- `filename`: Original filename
- `url`: Public URL to access the file
- `stats`: Comprehensive statistics
- `improvement_resume`: Improvement suggestions (if JD provided)

### Stats Object
- `overall_score`: Overall quality score (0-10)
- `sections`: Score breakdown by section
- `strengths`: List of identified strengths
- `weaknesses`: List of areas for improvement
- `recommendations`: Actionable recommendations
- `ats_compatibility`: ATS system compatibility analysis
- `keyword_analysis`: Keyword matching analysis

### Improvement Resume Object (when JD provided)
- `fit_score`: Job fit score (0-100)
- `matching_skills`: Skills that match the JD
- `missing_skills`: Skills missing from resume
- `suggestions`: Specific improvement suggestions
- `rewritten_sections`: AI-improved resume sections
- `overall_improvement_score`: Projected score after improvements
- `recommendations`: High-level recommendations

## Examples

### Example 1: Upload Resume Only

```bash
curl -X POST "http://localhost:8000/v1/resume/upload" \
  -F "file=@resume.pdf" \
  -F "user_id=user123"
```

**Response**: Basic CV quality analysis without job matching

### Example 2: Upload Resume with Job Description

```bash
curl -X POST "http://localhost:8000/v1/resume/upload" \
  -F "file=@resume.pdf" \
  -F "user_id=user123" \
  -F "jd_text=Senior Full Stack Developer with 5+ years experience in React, Node.js, TypeScript, MongoDB, and AWS. Must have experience with microservices and CI/CD."
```

**Response**: Complete analysis including job fit, matching skills, and improvement suggestions

### Example 3: JavaScript/TypeScript

```typescript
const uploadResume = async (file: File, userId: string, jdText?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);
  if (jdText) {
    formData.append('jd_text', jdText);
  }

  const response = await fetch('http://localhost:8000/v1/resume/upload', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return await response.json();
};

// Usage
const result = await uploadResume(
  resumeFile, 
  'user123',
  'Senior Developer position...'
);

console.log('Resume ID:', result.resume.id);
console.log('Overall Score:', result.resume.stats.overall_score);
console.log('Strengths:', result.resume.stats.strengths);
console.log('Recommendations:', result.resume.stats.recommendations);
```

## Error Responses

### 400 - Bad Request
```json
{
  "detail": "Invalid file format. Supported formats: PDF, DOCX, DOC, TXT"
}
```

### 500 - Server Error
```json
{
  "detail": "Upload failed: [error message]"
}
```

## Notes

1. **File Formats**: Supports PDF, DOCX, DOC, TXT, RTF, HTML, ODT
2. **File Size**: Maximum 10MB recommended
3. **Processing Time**: 2-5 seconds for basic analysis, 5-10 seconds with JD matching
4. **Storage**: Files are stored in `uploads/users/{user_id}/` directory
5. **Database**: Resume metadata stored in MongoDB
6. **URL**: File URL is relative to your frontend server (adjust as needed)

## Integration Tips

1. **Show Progress**: Display loading indicator during upload
2. **Validate File**: Check file type and size before uploading
3. **Handle Errors**: Provide user-friendly error messages
4. **Display Results**: Show scores, strengths, and recommendations in UI
5. **Save Resume ID**: Store the resume ID for future reference

## Related Endpoints

- `GET /v1/sessions/resume/{resume_id}` - Get resume details
- `POST /v1/cv/score` - Score CV from text
- `POST /v1/cv/fit-index` - Get fit index for CV + JD
- `POST /v1/cv/improvement` - Get improvement suggestions
