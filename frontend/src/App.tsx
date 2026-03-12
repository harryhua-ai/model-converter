import { Router } from 'preact-router';
import HomePage from './pages/HomePage';
import SetupPage from './pages/SetupPage';

export function App() {
  return (
    <Router>
      <HomePage path="/" />
      <SetupPage path="/setup" />
    </Router>
  );
}
