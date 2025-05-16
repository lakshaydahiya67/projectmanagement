# Project Management Frontend

This is the React frontend for the Project Management application, providing a user-friendly interface for managing projects, tasks, and collaboration.

## Features

- **Project Dashboard**: Overview of all projects and key metrics
- **Task Board**: Kanban-style board with drag-and-drop functionality
- **Real-time Collaboration**: WebSocket integration for live updates
- **User Management**: Profile settings and preferences
- **Notifications**: In-app notification system
- **Analytics**: Visual charts and reports
- **Responsive Design**: Works on desktop and mobile
- **Dark Mode**: Customizable theme preferences

## Technology Stack

- React 18.2.0
- React Router 6
- Redux for state management
- Tailwind CSS for styling
- Chart.js for data visualization
- React Beautiful DND for drag-and-drop
- Axios for API communication
- Socket.io for WebSocket communication

## Prerequisites

- Node.js 16+
- NPM 8+
- Backend API running (see main project README)

## Getting Started

### Installation

1. Clone the repository (if not already done)
2. Navigate to the frontend directory:
   ```bash
   cd projectmanagement/frontend
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Setup environment:
   ```bash
   cp .env-example .env
   ```
   
   Edit the `.env` file to set your environment variables:
   - `REACT_APP_API_URL`: URL of the backend API
   - `REACT_APP_WEBSOCKET_URL`: URL for WebSocket connection
   - Other settings as needed

### Development

Run the development server:

```bash
npm start
```

The application will be available at http://localhost:3000.

### Building for Production

```bash
npm run build
```

This creates a `build` directory with optimized production files.

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/             # API client functions
│   ├── components/      # Reusable UI components
│   │   ├── common/      # Generic components
│   │   ├── dashboard/   # Dashboard components
│   │   ├── projects/    # Project-related components
│   │   └── tasks/       # Task-related components
│   ├── context/         # React contexts
│   ├── hooks/           # Custom hooks
│   ├── pages/           # Page components
│   ├── reducers/        # Redux reducers
│   ├── services/        # Service functions
│   ├── styles/          # CSS and style files
│   ├── utils/           # Utility functions
│   ├── App.js           # Main app component
│   └── index.js         # Entry point
└── package.json         # Dependencies and scripts
```

## Key Components

### Authentication

Authentication is handled using JWT tokens stored in browser localStorage. Login and registration are managed through the authentication API endpoints.

### WebSocket Integration

Real-time updates are implemented using WebSockets. The connection is established in the WebSocketProvider component and manages events like task updates, comments, and notifications.

### State Management

Application state is managed with Redux, with actions and reducers organized by feature domain (projects, tasks, users, etc.).

## Testing

Run tests with:

```bash
npm test
```

For coverage report:

```bash
npm test -- --coverage
```

## Linting and Formatting

Run ESLint:

```bash
npm run lint
```

Fix ESLint issues:

```bash
npm run lint:fix
```

Format code with Prettier:

```bash
npm run format
```

## Contributing

Please see the [Contributing Guide](../docs/CONTRIBUTING.md) for details on how to contribute to the project.

## Troubleshooting

For common issues and solutions, see the [Troubleshooting Guide](../docs/TROUBLESHOOTING.md).
