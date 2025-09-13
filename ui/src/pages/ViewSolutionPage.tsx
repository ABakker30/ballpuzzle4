import React, { useState } from 'react';
import { SolutionViewer3D } from '../components/solution/SolutionViewer3D';
import { SolutionToolbar } from '../components/solution/SolutionToolbar';
import { SolutionJson } from '../types/solution';

export const ViewSolutionPage: React.FC = () => {
  const [solution, setSolution] = useState<SolutionJson | null>(null);
  const [maxPlacements, setMaxPlacements] = useState<number>(Infinity);
  const handleLoadSolution = (solutionData: SolutionJson) => {
    setSolution(solutionData);
    setMaxPlacements(solutionData.placements?.length || 0);
  };

  return (
    <div style={{ display: 'grid', gap: '16px', height: '100%' }}>
      <h2>View Solution</h2>
      
      <SolutionToolbar
        onLoadSolution={handleLoadSolution}
        solution={solution}
        maxPlacements={maxPlacements}
        onMaxPlacementsChange={setMaxPlacements}
      />
      
      <SolutionViewer3D 
        solution={solution}
        maxPlacements={maxPlacements}
        brightness={2.0}
        orientToSurface={true}
        resetTrigger={0}
      />
    </div>
  );
};
