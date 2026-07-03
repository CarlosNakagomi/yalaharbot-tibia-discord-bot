import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import CharacterManager from './components/CharacterManager';
import Home from './components/Home';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-blue-600 p-4">
          <ul className="flex space-x-4 justify-center text-white">
            <li>
              <Link to="/" className="hover:text-blue-300 font-semibold">
                Home
              </Link>
            </li>
            <li>
              <Link to="/characters" className="hover:text-blue-300 font-semibold">
                Characters
              </Link>
            </li>
          </ul>
        </nav>

        <div className="container mx-auto p-8">
          <Routes>
            <Route path="/characters" element={<CharacterManager />} />
            <Route path="/" element={<Home />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
