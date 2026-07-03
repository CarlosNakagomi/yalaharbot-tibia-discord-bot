import React from 'react';

function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-r from-blue-500 to-indigo-500 flex flex-col items-center justify-center text-white">
      <h1 className="text-4xl font-bold mb-4">Welcome to Tibia Character Manager</h1>
      <p className="text-lg mb-8">
        Manage your Tibia characters with ease. Track levels, update information, and much more.
      </p>
      <button className="bg-white text-blue-500 font-semibold py-2 px-4 rounded shadow-lg hover:bg-gray-100 transition duration-300">
        Get Started
      </button>
    </div>
  );
}

export default Home;
