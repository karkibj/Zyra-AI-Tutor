import React, { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import {
  X,
  Download,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Minimize2,
} from "lucide-react";
import axios from "axios";

import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import "../styles/PDFViewer.css";

// ✅ FIXED: Use local worker file from public folder
pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

interface PDFViewerProps {
  paper: {
    id: string;
    title: string;
    year: number;
    province: string;
    download_url: string;
  };
  onClose: () => void;
  onDownload: () => void;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ paper, onClose, onDownload }) => {
  const [numPages, setNumPages]           = useState(0);
  const [pageNumber, setPageNumber]       = useState(1);
  const [scale, setScale]                 = useState(1);
  const [isFullscreen, setIsFullscreen]   = useState(false);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState(false);
  const [pdfBlobUrl, setPdfBlobUrl]       = useState<string | null>(null);

  useEffect(() => {
    let objectUrl: string;
    setLoading(true);
    setError(false);

    axios
      .get(`http://localhost:8000${paper.download_url}`, { responseType: "blob" })
      .then((res) => {
        objectUrl = window.URL.createObjectURL(
          new Blob([res.data], { type: "application/pdf" })
        );
        setPdfBlobUrl(objectUrl);
      })
      .catch((err) => {
        console.error("PDF load error:", err);
        setError(true);
        setLoading(false);
      });

    return () => {
      if (objectUrl) window.URL.revokeObjectURL(objectUrl);
    };
  }, [paper.download_url]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
  };

  const onDocumentLoadError = () => {
    setError(true);
    setLoading(false);
  };

  const goToPrevPage     = () => setPageNumber((p) => Math.max(1, p - 1));
  const goToNextPage     = () => setPageNumber((p) => Math.min(numPages, p + 1));
  const zoomIn           = () => setScale((s) => Math.min(2,   +(s + 0.2).toFixed(1)));
  const zoomOut          = () => setScale((s) => Math.max(0.5, +(s - 0.2).toFixed(1)));
  const toggleFullscreen = () => setIsFullscreen((f) => !f);

  return (
    <div
      className={`pdf-viewer-overlay ${isFullscreen ? "fullscreen" : ""}`}
      onClick={onClose}
    >
      <div className="pdf-viewer-container" onClick={(e) => e.stopPropagation()}>

        <div className="pdf-viewer-header">
          <div className="pdf-info">
            <h2>{paper.title}</h2>
            <p>SEE {paper.year} – {paper.province} Province</p>
          </div>
          <div className="pdf-header-actions">
            <button className="icon-btn" onClick={onDownload} title="Download">
              <Download size={20} />
            </button>
            <button className="icon-btn" onClick={toggleFullscreen} title="Fullscreen">
              {isFullscreen ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
            </button>
            <button className="icon-btn close-btn" onClick={onClose} title="Close">
              <X size={24} />
            </button>
          </div>
        </div>

        <div className="pdf-viewer-controls">
          <div className="page-controls">
            <button onClick={goToPrevPage} disabled={pageNumber <= 1}>
              <ChevronLeft size={20} />
            </button>
            <span>{pageNumber} / {numPages || "?"}</span>
            <button onClick={goToNextPage} disabled={pageNumber >= numPages}>
              <ChevronRight size={20} />
            </button>
          </div>
          <div className="zoom-controls">
            <button onClick={zoomOut} disabled={scale <= 0.5}>
              <ZoomOut size={20} />
            </button>
            <span>{Math.round(scale * 100)}%</span>
            <button onClick={zoomIn} disabled={scale >= 2}>
              <ZoomIn size={20} />
            </button>
          </div>
        </div>

        <div className="pdf-viewer-content">
          {loading && !error && (
            <div className="pdf-loading">
              <div className="pdf-spinner" />
              <p>Loading PDF…</p>
            </div>
          )}
          {error && (
            <div className="pdf-error">
              <p>⚠️ Could not load PDF preview.</p>
              <button onClick={onDownload} className="pdf-download-fallback">
                <Download size={16} /> Download instead
              </button>
            </div>
          )}
          {pdfBlobUrl && !error && (
            <Document
              file={pdfBlobUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading=""
            >
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer
                renderAnnotationLayer
              />
            </Document>
          )}
        </div>

      </div>
    </div>
  );
};

export default PDFViewer;