import React, { useState, useCallback, useRef } from 'react';
import { Upload, X, CheckCircle, AlertCircle, FileText, Loader } from 'lucide-react';

interface UploadTabProps {
  onUploadComplete: () => void;
}

interface Chapter {
  code: string;
  name: string;
  number: number;
}

const CONTENT_TYPES = [
  { value: 'curriculum', label: 'Curriculum Material', description: 'Textbook chapters, syllabus' },
  { value: 'past_paper', label: 'Past Paper', description: 'SEE exam papers' },
  { value: 'model_question', label: 'Model Question', description: 'Practice questions' },
  { value: 'solution', label: 'Solution', description: 'Worked solutions' },
  { value: 'explanation', label: 'Explanation', description: 'Concept explanations' },
  { value: 'teacher_note', label: 'Teacher Notes', description: 'Teaching materials' }
];

const CHAPTERS: Chapter[] = [
  { code: 'CDC-10-MATH-CH01', name: 'Sets', number: 1 },
  { code: 'CDC-10-MATH-CH02', name: 'Compound Interest', number: 2 },
  { code: 'CDC-10-MATH-CH03', name: 'Growth and Depreciation', number: 3 },
  { code: 'CDC-10-MATH-CH04', name: 'Currency and Exchange Rate', number: 4 },
  { code: 'CDC-10-MATH-CH05', name: 'Area and Volume', number: 5 },
  { code: 'CDC-10-MATH-CH06', name: 'Sequence and Series', number: 6 },
  { code: 'CDC-10-MATH-CH07', name: 'Quadratic Equation', number: 7 },
  { code: 'CDC-10-MATH-CH08', name: 'Algebraic Fraction', number: 8 },
  { code: 'CDC-10-MATH-CH09', name: 'Indices', number: 9 },
  { code: 'CDC-10-MATH-CH10', name: 'Triangles and Quadrilaterals', number: 10 },
  { code: 'CDC-10-MATH-CH11', name: 'Construction', number: 11 },
  { code: 'CDC-10-MATH-CH12', name: 'Circle', number: 12 },
  { code: 'CDC-10-MATH-CH13', name: 'Statistics', number: 13 },
  { code: 'CDC-10-MATH-CH14', name: 'Probability', number: 14 }
];

export const UploadTab: React.FC<UploadTabProps> = ({ onUploadComplete }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // Form fields
  const [title, setTitle] = useState('');
  const [contentType, setContentType] = useState('curriculum');
  const [description, setDescription] = useState('');
  const [selectedChapters, setSelectedChapters] = useState<string[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-detect content type and suggest chapters
  const autoDetectFromFilename = (filename: string) => {
    const lower = filename.toLowerCase();
    
    // Detect past papers
    if (lower.includes('2081') || lower.includes('2080') || lower.includes('see')) {
      setContentType('past_paper');
      // Select all chapters for past papers
      setSelectedChapters(CHAPTERS.map(ch => ch.code));
      
      // Auto-generate title
      if (lower.includes('bagmati')) {
        setTitle('SEE 2081 Mathematics - Bagmati Province');
      } else if (lower.includes('gandaki')) {
        setTitle('SEE 2081 Mathematics - Gandaki Province');
      }
    }
    
    // Detect model questions
    else if (lower.includes('model')) {
      setContentType('model_question');
      setSelectedChapters(CHAPTERS.map(ch => ch.code));
    }
    
    // Detect chapter-specific content
    else {
      CHAPTERS.forEach(chapter => {
        const chapterName = chapter.name.toLowerCase().replace(/\s+/g, '_');
        if (lower.includes(chapterName) || lower.includes(`ch${chapter.number}`)) {
          setSelectedChapters([chapter.code]);
          setTitle(`${chapter.name} - Study Material`);
        }
      });
    }
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
        autoDetectFromFilename(file.name);
      } else {
        setUploadError('Please upload a PDF file');
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'application/pdf') {
        setSelectedFile(file);
        autoDetectFromFilename(file.name);
      } else {
        setUploadError('Please upload a PDF file');
      }
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    setTitle('');
    setDescription('');
    setSelectedChapters([]);
    setTags([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const toggleChapter = (code: string) => {
    setSelectedChapters(prev =>
      prev.includes(code)
        ? prev.filter(c => c !== code)
        : [...prev, code]
    );
  };

  const selectAllChapters = () => {
    setSelectedChapters(CHAPTERS.map(ch => ch.code));
  };

  const clearAllChapters = () => {
    setSelectedChapters([]);
  };

  const addTag = () => {
    if (tagInput.trim() && !tags.includes(tagInput.trim())) {
      setTags([...tags, tagInput.trim()]);
      setTagInput('');
    }
  };

  const removeTag = (tag: string) => {
    setTags(tags.filter(t => t !== tag));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedFile || !title || selectedChapters.length === 0) {
      setUploadError('Please fill all required fields');
      return;
    }

    setUploading(true);
    setUploadError(null);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title);
      formData.append('content_type', contentType);
      formData.append('description', description);
      formData.append('curriculum_codes', JSON.stringify(selectedChapters));
      formData.append('tags', JSON.stringify(tags));

      const response = await fetch('http://localhost:8000/api/v1/admin/content/upload', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      setUploadSuccess(true);
      setTimeout(() => {
        removeFile();
        setUploadSuccess(false);
        onUploadComplete();
      }, 2000);

    } catch (error) {
      setUploadError('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <h2>Upload Content</h2>
        <p>Upload educational materials to the knowledge base</p>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        {/* File Upload Area */}
        <div
          className={`upload-dropzone ${isDragging ? 'dragging' : ''} ${selectedFile ? 'has-file' : ''}`}
          onDragEnter={handleDragEnter}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />

          {!selectedFile ? (
            <>
              <Upload className="upload-icon" />
              <h3>Drop PDF file here or click to browse</h3>
              <p>Support for PDF files only</p>
            </>
          ) : (
            <div className="upload-file-info">
              <FileText className="file-icon" />
              <div className="file-details">
                <h4>{selectedFile.name}</h4>
                <p>{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile();
                }}
                className="remove-file-btn"
              >
                <X />
              </button>
            </div>
          )}
        </div>

        {selectedFile && (
          <>
            {/* Title */}
            <div className="form-group">
              <label className="form-label required">Title</label>
              <input
                type="text"
                className="form-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g., SEE 2081 Bagmati Mathematics"
                required
              />
            </div>

            {/* Content Type */}
            <div className="form-group">
              <label className="form-label required">Content Type</label>
              <div className="content-type-grid">
                {CONTENT_TYPES.map((type) => (
                  <div
                    key={type.value}
                    className={`content-type-card ${contentType === type.value ? 'selected' : ''}`}
                    onClick={() => setContentType(type.value)}
                  >
                    <div className="content-type-header">
                      <input
                        type="radio"
                        name="contentType"
                        value={type.value}
                        checked={contentType === type.value}
                        onChange={() => setContentType(type.value)}
                      />
                      <strong>{type.label}</strong>
                    </div>
                    <p>{type.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Description */}
            <div className="form-group">
              <label className="form-label">Description (Optional)</label>
              <textarea
                className="form-textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add any additional details..."
                rows={3}
              />
            </div>

            {/* Chapters Selection */}
            <div className="form-group">
              <div className="chapters-header">
                <label className="form-label required">Map to Chapters</label>
                <div className="chapters-actions">
                  <button type="button" onClick={selectAllChapters} className="link-btn">
                    Select All
                  </button>
                  <button type="button" onClick={clearAllChapters} className="link-btn">
                    Clear All
                  </button>
                </div>
              </div>
              <div className="chapters-grid">
                {CHAPTERS.map((chapter) => (
                  <div
                    key={chapter.code}
                    className={`chapter-card ${selectedChapters.includes(chapter.code) ? 'selected' : ''}`}
                    onClick={() => toggleChapter(chapter.code)}
                  >
                    <input
                      type="checkbox"
                      checked={selectedChapters.includes(chapter.code)}
                      onChange={() => toggleChapter(chapter.code)}
                    />
                    <span className="chapter-number">Ch {chapter.number}</span>
                    <span className="chapter-name">{chapter.name}</span>
                  </div>
                ))}
              </div>
              <p className="form-hint">{selectedChapters.length} chapter(s) selected</p>
            </div>

            {/* Tags */}
            <div className="form-group">
              <label className="form-label">Tags (Optional)</label>
              <div className="tags-input-wrapper">
                <input
                  type="text"
                  className="form-input"
                  value={tagInput}
                  onChange={(e) => setTagInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                  placeholder="Add tags... (press Enter)"
                />
                <button type="button" onClick={addTag} className="add-tag-btn">
                  Add
                </button>
              </div>
              {tags.length > 0 && (
                <div className="tags-list">
                  {tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                      <button type="button" onClick={() => removeTag(tag)}>
                        <X size={14} />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Error/Success Messages */}
            {uploadError && (
              <div className="alert alert-error">
                <AlertCircle />
                <span>{uploadError}</span>
              </div>
            )}

            {uploadSuccess && (
              <div className="alert alert-success">
                <CheckCircle />
                <span>Upload successful! Content added to knowledge base.</span>
              </div>
            )}

            {/* Submit Button */}
            <div className="form-actions">
              <button
                type="button"
                onClick={removeFile}
                className="btn btn-secondary"
                disabled={uploading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={uploading || !title || selectedChapters.length === 0}
              >
                {uploading ? (
                  <>
                    <Loader className="spinner" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload />
                    Upload Content
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </form>
    </div>
  );
};

export default UploadTab;