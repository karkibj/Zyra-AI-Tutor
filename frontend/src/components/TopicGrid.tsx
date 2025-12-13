import React from 'react';
import { useNavigate } from 'react-router-dom';

interface TopicGridProps {
  topics: string[];
}

const TopicGrid: React.FC<TopicGridProps> = ({ topics }) => {
  const navigate = useNavigate();

  const handleTopicClick = (topic: string) => {
    navigate('/chat', { state: { selectedTopic: topic } });
  };

  return (
    <div className="topics-grid">
      {topics.map((topic, index) => (
        <button
          key={index}
          className="topic-btn"
          onClick={() => handleTopicClick(topic)}
        >
          <span>{topic}</span>
        </button>
      ))}
    </div>
  );
};

export default TopicGrid;