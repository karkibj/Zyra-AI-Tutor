import React, { useState } from 'react';
import { Upload, X, Check, AlertCircle } from 'lucide-react';

type ContentType = 'curriculum' | 'past_paper' | 'model_question' | 'solution' | 'explanation' | 'teacher_note';

interface Chapter {
  id: string;
  name: string;
  number: number;
}

interface UploadTabProps {
  onUploadSuccess?: () => void;
}

export const UploadTab: React.FC<UploadTabProps> = ({ onUploadSuccess }) => {
  // Form state
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState<ContentType>('curriculum');
  const [description, setDescription] = useState('');
  const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  
  // NEW: Metadata state
  const [province, setProvince] = useState('');
  const [year, setYear] = useState('');
  const [examType, setExamType] = useState('');
  
  // UI state
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 14 CDC Grade 10 Math Chapters
  const chapters: Chapter[] = [
    { id: 'ch01', name: 'Sets', number: 1 },
    { id: 'ch02', name: 'Compound Interest', number: 2 },
    { id: 'ch03', name: 'Growth and Depreciation', number: 3 },
    { id: 'ch04', name: 'Currency and Exchange Rate', number: 4 },
    { id: 'ch05', name: 'Area and Volume', number: 5 },
    { id: 'ch06', name: 'Sequence and Series', number: 6 },
    { id: 'ch07', name: 'Quadratic Equation', number: 7 },
    { id: 'ch08', name: 'Algebraic Fraction', number: 8 },
    { id: 'ch09', name: 'Indices', number: 9 },
    { id: 'ch10', name: 'Triangles and Quadrilaterals', number: 10 },
    { id: 'ch11', name: 'Construction', number: 11 },
    { id: 'ch12', name: 'Circle', number: 12 },
    { id: 'ch13', name: 'Statistics', number: 13 },
    { id: 'ch14', name: 'Probability', number: 14 },
  ];

  // ========================================================================
  // INTELLIGENT AUTO-DETECTION FROM FILENAME
  // ========================================================================
  
  const detectMetadataFromFilename = (filename: string) => {
    const lower = filename.toLowerCase();
    
    let detectedData = {
      title: filename.replace(/\.[^/.]+$/, ''), // Remove extension
      contentType: 'curriculum' as ContentType,
      chapters: [] as string[],
      tags: [] as string[],
      description: '',
      province: '',
      year: '',
      examType: ''
    };

    // ===== DETECT YEAR (2078, 2079, 2080, 2081, etc.) =====
    const yearMatch = lower.match(/20(\d{2})/);
    if (yearMatch) {
      detectedData.year = `20${yearMatch[1]}`;
      detectedData.tags.push(detectedData.year);
    }

    // ===== DETECT PROVINCE =====
    const provinceMap: Record<string, string> = {
      'bagmati': 'Bagmati',
      'gandaki': 'Gandaki',
      'koshi': 'Koshi',
      'madhesh': 'Madhesh',
      'lumbini': 'Lumbini',
      'karnali': 'Karnali',
      'sudurpashchim': 'Sudurpashchim',
      'sudurpaschim': 'Sudurpashchim',
      'province1': 'Province 1',
      'province2': 'Province 2',
      'province 1': 'Province 1',
      'province 2': 'Province 2',
      'allprovince': 'All Provinces',
      'all province': 'All Provinces'
    };

    for (const [key, value] of Object.entries(provinceMap)) {
      if (lower.includes(key)) {
        detectedData.province = value;
        detectedData.tags.push(value.toLowerCase().replace(' ', '_'));
        break;
      }
    }

    // ===== DETECT EXAM TYPE =====
    if (lower.includes('model') && lower.includes('question')) {
      detectedData.examType = 'model_question';
      detectedData.contentType = 'model_question';
      detectedData.tags.push('model', 'practice');
    } else if (lower.includes('see') || lower.includes('past') || lower.includes('previous')) {
      detectedData.examType = 'past_paper';
      detectedData.contentType = 'past_paper';
      detectedData.tags.push('past_paper', 'see', 'exam');
    } else if (lower.includes('solution') || lower.includes('answer')) {
      detectedData.contentType = 'solution';
      detectedData.tags.push('solution', 'answers');
    } else if (lower.includes('note')) {
      detectedData.contentType = 'teacher_note';
      detectedData.tags.push('notes', 'teaching');
    } else if (lower.includes('cdc') || lower.includes('curriculum') || lower.includes('textbook')) {
      detectedData.contentType = 'curriculum';
      detectedData.tags.push('curriculum', 'cdc', 'textbook');
    }

    // ===== BUILD SMART TITLE =====
    if (detectedData.province && detectedData.year && detectedData.examType === 'past_paper') {
      detectedData.title = `SEE ${detectedData.year} Mathematics - ${detectedData.province} Province`;
      detectedData.description = `Official SEE examination paper from ${detectedData.province} Province, year ${detectedData.year}`;
    } else if (detectedData.province && detectedData.year && detectedData.examType === 'model_question') {
      detectedData.title = `SEE ${detectedData.year} Model Questions - ${detectedData.province} Province`;
      detectedData.description = `Model question set for SEE ${detectedData.year} preparation (${detectedData.province} Province)`;
    } else if (detectedData.year && detectedData.examType === 'model_question') {
      detectedData.title = `SEE ${detectedData.year} Model Questions - Mathematics`;
      detectedData.description = `Model question set for SEE ${detectedData.year} preparation`;
    } else if (detectedData.year && detectedData.examType === 'past_paper') {
      detectedData.title = `SEE ${detectedData.year} Mathematics Past Paper`;
      detectedData.description = `SEE ${detectedData.year} examination paper`;
    } else if (lower.includes('cdc') || lower.includes('textbook')) {
      detectedData.title = 'CDC Grade 10 Mathematics Textbook';
      detectedData.description = 'Official CDC curriculum textbook for Grade 10 Mathematics';
    }

    // ===== AUTO-SELECT CHAPTERS =====
    // Past papers and model questions cover ALL chapters
    if (detectedData.contentType === 'past_paper' || detectedData.contentType === 'model_question') {
      detectedData.chapters = chapters.map(c => c.id);
    }
    
    // CDC textbook covers ALL chapters
    if (lower.includes('cdc') || lower.includes('textbook') || lower.includes('curriculum')) {
      detectedData.chapters = chapters.map(c => c.id);
    }

    // Detect specific chapters in filename
    const chapterPatterns = [
      { pattern: /chapter\s*(\d+)/i, chapters: [] as string[] },
      { pattern: /ch\s*(\d+)/i, chapters: [] as string[] },
      { pattern: /unit\s*(\d+)/i, chapters: [] as string[] },
    ];

    for (const { pattern } of chapterPatterns) {
      const matches = filename.match(pattern);
      if (matches) {
        const chapterNum = parseInt(matches[1]);
        const chapter = chapters.find(c => c.number === chapterNum);
        if (chapter && !detectedData.chapters.includes(chapter.id)) {
          detectedData.chapters.push(chapter.id);
        }
      }
    }

    return detectedData;
  };

  // ========================================================================
  // FILE UPLOAD HANDLERS
  // ========================================================================

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const processFile = (file: File) => {
    // Validate file type
    if (file.type !== 'application/pdf') {
      setError('Please upload a PDF file');
      return;
    }

    setSelectedFile(file);
    setError(null);
    setSuccess(null);

    // Auto-detect metadata from filename
    const detected = detectMetadataFromFilename(file.name);
    
    setTitle(detected.title);
    setContentType(detected.contentType);
    setDescription(detected.description);
    setSelectedChapters(detected.chapters);
    setTags(detected.tags);
    setProvince(detected.province);
    setYear(detected.year);
    setExamType(detected.examType);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  // ========================================================================
  // CHAPTER SELECTION
  // ========================================================================

  const toggleChapter = (chapterId: string) => {
    setSelectedChapters(prev =>
      prev.includes(chapterId)
        ? prev.filter(id => id !== chapterId)
        : [...prev, chapterId]
    );
  };

  const selectAllChapters = () => {
    setSelectedChapters(chapters.map(c => c.id));
  };

  const clearAllChapters = () => {
    setSelectedChapters([]);
  };

  // ========================================================================
  // TAGS MANAGEMENT
  // ========================================================================

  const addTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().toLowerCase();
      if (!tags.includes(newTag)) {
        setTags([...tags, newTag]);
      }
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  // ========================================================================
  // FORM SUBMISSION
  // ========================================================================

  const handleSubmit = async () => {
    // Validation
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a title');
      return;
    }

    if (selectedChapters.length === 0) {
      setError('Please select at least one chapter');
      return;
    }

    setIsUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title);
      formData.append('content_type', contentType);
      formData.append('description', description);
      formData.append('chapter_ids', JSON.stringify(selectedChapters));
      formData.append('tags', JSON.stringify(tags));

      // Add comprehensive metadata
      const metadata = {
        province: province || 'Unknown',
        year: year || new Date().getFullYear().toString(),
        exam_type: examType || contentType,
        uploaded_via: 'admin_dashboard',
        auto_detected: !!(province || year),
        upload_timestamp: new Date().toISOString(),
        file_original_name: selectedFile.name
      };
      formData.append('metadata', JSON.stringify(metadata));

      const response = await fetch('http://localhost:8000/api/v1/admin/content/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();
      
      setSuccess(`✅ Successfully uploaded: ${title}`);
      
      console.log('✅ Upload successful:', result);

      // Reset form
      setSelectedFile(null);
      setTitle('');
      setDescription('');
      setSelectedChapters([]);
      setTags([]);
      setProvince('');
      setYear('');
      setExamType('');
      setContentType('curriculum');
      
      // Refresh dashboard
      if (onUploadSuccess) {
        setTimeout(() => {
          onUploadSuccess();
        }, 1000);
      }

    } catch (err) {
      console.error('Upload error:', err);
      setError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  // ========================================================================
  // RENDER
  // ========================================================================

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>Upload Content</h2>
        <p>Upload PDFs for processing and indexing</p>
      </div>

      {/* Dropzone */}
      <div
        className={`upload-dropzone ${isDragging ? 'dragging' : ''} ${selectedFile ? 'has-file' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />

        {!selectedFile ? (
          <>
            <Upload className="upload-icon" />
            <h3>Drag & drop your PDF here</h3>
            <p>or click to browse</p>
            <span className="file-types">Supported: PDF files only</span>
          </>
        ) : (
          <div className="upload-file-info">
            <Check className="check-icon" />
            <div>
              <h4>{selectedFile.name}</h4>
              <p>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
            <button
              className="remove-file-btn"
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                setTitle('');
                setDescription('');
                setProvince('');
                setYear('');
              }}
            >
              <X size={20} />
            </button>
          </div>
        )}
      </div>

      {/* Auto-Detected Metadata Display */}
      {selectedFile && (province || year || examType) && (
        <div className="detected-metadata">
          <h4>🔍 Auto-Detected Information</h4>
          <div className="metadata-tags">
            {province && <span className="meta-tag">📍 {province} Province</span>}
            {year && <span className="meta-tag">📅 Year {year}</span>}
            {examType && <span className="meta-tag">📄 {examType.replace('_', ' ')}</span>}
            {selectedChapters.length > 0 && (
              <span className="meta-tag">📚 {selectedChapters.length} chapters selected</span>
            )}
          </div>
          <p className="meta-hint">💡 Auto-detection can be edited below</p>
        </div>
      )}

      {selectedFile && (
        <div className="upload-form">
          {/* Title */}
          <div className="form-group">
            <label>Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., SEE 2081 Mathematics - Gandaki Province"
              className="form-input"
            />
          </div>

          {/* Content Type */}
          <div className="form-group">
            <label>Content Type *</label>
            <div className="content-type-grid">
              {[
                { value: 'curriculum', label: '📚 Curriculum', desc: 'Textbook, syllabus' },
                { value: 'past_paper', label: '📝 Past Paper', desc: 'Previous exams' },
                { value: 'model_question', label: '🎯 Model Question', desc: 'Practice sets' },
                { value: 'solution', label: '✅ Solution', desc: 'Worked answers' },
                { value: 'explanation', label: '💡 Explanation', desc: 'Concept guides' },
                { value: 'teacher_note', label: '👨‍🏫 Teacher Note', desc: 'Teaching materials' },
              ].map((type) => (
                <div
                  key={type.value}
                  className={`type-card ${contentType === type.value ? 'selected' : ''}`}
                  onClick={() => setContentType(type.value as ContentType)}
                >
                  <div className="type-label">{type.label}</div>
                  <div className="type-desc">{type.desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="form-group">
            <label>Description (Optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the content..."
              className="form-textarea"
              rows={3}
            />
          </div>

          {/* Chapter Mapping */}
          <div className="form-group">
            <label>
              Map to Chapters * 
              <span className="chapter-count">({selectedChapters.length} selected)</span>
            </label>
            <div className="chapter-actions">
              <button type="button" onClick={selectAllChapters} className="btn-secondary-sm">
                Select All
              </button>
              <button type="button" onClick={clearAllChapters} className="btn-secondary-sm">
                Clear All
              </button>
            </div>
            <div className="chapters-grid">
              {chapters.map((chapter) => (
                <label key={chapter.id} className="chapter-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedChapters.includes(chapter.id)}
                    onChange={() => toggleChapter(chapter.id)}
                  />
                  <span className="chapter-label">
                    <span className="chapter-num">Ch {chapter.number}</span>
                    {chapter.name}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Tags */}
          <div className="form-group">
            <label>Tags (Optional)</label>
            <input
              type="text"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={addTag}
              placeholder="Type a tag and press Enter"
              className="form-input"
            />
            {tags.length > 0 && (
              <div className="tags-list">
                {tags.map((tag) => (
                  <span key={tag} className="tag">
                    {tag}
                    <button onClick={() => removeTag(tag)} className="tag-remove">
                      <X size={14} />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Error/Success Messages */}
          {error && (
            <div className="alert alert-error">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              <Check size={20} />
              <span>{success}</span>
            </div>
          )}

          {/* Submit Buttons */}
          <div className="form-actions">
            <button
              type="button"
              onClick={() => {
                setSelectedFile(null);
                setTitle('');
                setDescription('');
                setSelectedChapters([]);
                setTags([]);
                setProvince('');
                setYear('');
              }}
              className="btn btn-secondary"
              disabled={isUploading}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              className="btn btn-primary"
              disabled={isUploading || !selectedFile || !title || selectedChapters.length === 0}
            >
              {isUploading ? 'Uploading...' : 'Upload & Process'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadTab;