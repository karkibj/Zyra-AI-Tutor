import React, { useState, useEffect } from 'react';
import { FolderTree, ChevronRight, ChevronDown, FileText, Book } from 'lucide-react';

interface CurriculumNode {
  id: string;
  code: string;
  node_type: string;
  name: string;
  content_count: number;
  children: CurriculumNode[];
}

export const CurriculumTab: React.FC = () => {
  const [curriculumTree, setCurriculumTree] = useState<CurriculumNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set(['CDC', 'CDC-10', 'CDC-10-MATH']));

  useEffect(() => {
    fetchCurriculum();
  }, []);

  const fetchCurriculum = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/curriculum/tree?root_code=CDC');
      const data = await response.json();
      setCurriculumTree(data);
    } catch (error) {
      console.error('Error fetching curriculum:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleNode = (code: string) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(code)) {
        newSet.delete(code);
      } else {
        newSet.add(code);
      }
      return newSet;
    });
  };

  const renderNode = (node: CurriculumNode, level: number = 0) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedNodes.has(node.code);
    const isChapter = node.node_type === 'chapter';

    return (
      <div key={node.code} className="curriculum-node-wrapper">
        <div 
          className={`curriculum-node level-${level} ${isChapter ? 'chapter' : ''}`}
          onClick={() => hasChildren && toggleNode(node.code)}
        >
          <div className="node-left">
            {hasChildren && (
              <button className="node-toggle">
                {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
            )}
            {!hasChildren && <div className="node-spacer"></div>}
            
            <div className="node-icon">
              {node.node_type === 'board' && <FolderTree size={18} />}
              {node.node_type === 'grade' && <Book size={18} />}
              {node.node_type === 'subject' && <Book size={18} />}
              {node.node_type === 'chapter' && <FileText size={18} />}
            </div>
            
            <div className="node-content">
              <span className="node-name">{node.name}</span>
              <span className="node-type">{node.node_type}</span>
            </div>
          </div>

          <div className="node-right">
            <span className={`content-count ${node.content_count === 0 ? 'empty' : ''}`}>
              {node.content_count} content
            </span>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="node-children">
            {node.children.map(child => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="curriculum-container">
      <div className="curriculum-header">
        <div>
          <h2>Curriculum Structure</h2>
          <p>Browse the curriculum hierarchy and content distribution</p>
        </div>
        <button className="btn btn-primary" onClick={fetchCurriculum}>
          Refresh
        </button>
      </div>

      <div className="curriculum-tree">
        {curriculumTree && renderNode(curriculumTree)}
      </div>
    </div>
  );
};

export default CurriculumTab;