import React from 'react';
import { useContext } from 'react';
import { ThemeContext } from '../../context/ThemeContext';

const Logo = ({ className = 'h-8 w-auto' }) => {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === 'dark';
  
  return (
    <div className={`flex items-center ${className}`}>
      {/* App icon/logo SVG */}
      <svg 
        viewBox="0 0 24 24" 
        fill="none" 
        className={`h-full`}
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect 
          x="2" 
          y="2" 
          width="20" 
          height="20" 
          rx="5" 
          className="fill-blue-600 dark:fill-blue-500" 
        />
        <path 
          fillRule="evenodd" 
          clipRule="evenodd" 
          d="M7 8C7 7.44772 7.44772 7 8 7H16C16.5523 7 17 7.44772 17 8C17 8.55228 16.5523 9 16 9H8C7.44772 9 7 8.55228 7 8Z" 
          className="fill-white dark:fill-white"
        />
        <path 
          fillRule="evenodd" 
          clipRule="evenodd" 
          d="M7 12C7 11.4477 7.44772 11 8 11H16C16.5523 11 17 11.4477 17 12C17 12.5523 16.5523 13 16 13H8C7.44772 13 7 12.5523 7 12Z" 
          className="fill-white dark:fill-white" 
        />
        <path 
          fillRule="evenodd" 
          clipRule="evenodd" 
          d="M7 16C7 15.4477 7.44772 15 8 15H12C12.5523 15 13 15.4477 13 16C13 16.5523 12.5523 17 12 17H8C7.44772 17 7 16.5523 7 16Z" 
          className="fill-white dark:fill-white" 
        />
      </svg>
      
      {/* Text logo */}
      <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">TaskFlow</span>
    </div>
  );
};

export default Logo;
