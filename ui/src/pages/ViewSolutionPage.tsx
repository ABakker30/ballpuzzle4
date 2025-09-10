import React, { useState } from 'react';
import { SolutionViewer3D } from '../components/solution/SolutionViewer3D';
import { SolutionToolbar } from '../components/solution/SolutionToolbar';
import { SolutionJson } from '../types/solution';

export const ViewSolutionPage: React.FC = () => {
  const [solution, setSolution] = useState<SolutionJson | null>(null);
  const [maxPlacements, setMaxPlacements] = useState<number>(Infinity);
  const [brightness, setBrightness] = useState<number>(1.0);

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
        brightness={brightness}
        onBrightnessChange={setBrightness}
      />
      
      <SolutionViewer3D 
        solution={solution}
        maxPlacements={maxPlacements}
        brightness={brightness}
      />
      
      {solution && (
        <div className="card">
          <h3>Solution Details</h3>
          <div className="kpi-grid">
            <div className="kpi">
              <div className="kpi-label">Container CID</div>
              <div className="kpi-value">{solution.containerCidSha256?.slice(0, 12) || 'Unknown'}</div>
            </div>
            <div className="kpi">
              <div className="kpi-label">Lattice</div>
              <div className="kpi-value">{solution.lattice || 'fcc'}</div>
            </div>
            <div className="kpi">
              <div className="kpi-label">Engine</div>
              <div className="kpi-value">{solution.solver?.engine || 'Unknown'}</div>
            </div>
            <div className="kpi">
              <div className="kpi-label">Seed</div>
              <div className="kpi-value">{solution.solver?.seed || 'N/A'}</div>
            </div>
          </div>
          
          {solution.piecesUsed && (
            <div style={{ marginTop: '16px' }}>
              <h4>Pieces Used</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {Object.entries(solution.piecesUsed).map(([piece, count]) => (
                  <div key={piece} className="chip">
                    <span className="chip-label">{piece}:</span>
                    <span className="chip-value">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
