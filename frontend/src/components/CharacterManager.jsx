import React, { useState } from 'react';
import axios from 'axios';

const TibiaCharacter = () => {
  const [characterName, setCharacterName] = useState('');
  const [characterData, setCharacterData] = useState(null);
  const [error, setError] = useState('');

  const fetchCharacterData = async () => {
    try {
      const response = await axios.get(`/api/characters/fetch_tibia_data/?name=${characterName}`);
      setCharacterData(response.data);
      setError('');
    } catch (err) {
      setCharacterData(null);
      setError('Error fetching character data. Please try again.');
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Tibia Character Info</h2>
      <div className="mb-4">
        <input
          type="text"
          value={characterName}
          onChange={(e) => setCharacterName(e.target.value)}
          placeholder="Enter character name"
          className="border p-2 mr-2"
        />
        <button onClick={fetchCharacterData} className="bg-blue-500 text-white p-2 rounded">
          Fetch Character
        </button>
      </div>
      {error && <p className="text-red-500">{error}</p>}
      {characterData && (
        <div className="bg-gray-100 p-4 rounded">
          <h3 className="text-xl font-semibold">{characterData.name}</h3>
          <p>Level: {characterData.level}</p>
          <p>Vocation: {characterData.vocation}</p>
          <p>World: {characterData.world}</p>
          <p>Last Login: {characterData.last_login}</p>
          <p>Other Characters: </p>
          <ul className="list-disc list-inside">
        {characterData.other_characters.map((charName, index) => (
          <li key={index}>{charName}</li>
        ))}
      </ul>
        </div>
      )}
    </div>
  );
};

export default TibiaCharacter;