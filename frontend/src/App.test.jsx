import { render, screen } from '@testing-library/react';
import App from './App';

test('renders the home screen', () => {
  render(<App />);
  expect(screen.getByText(/Welcome to Tibia Character Manager/i)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Characters/i })).toBeInTheDocument();
});
