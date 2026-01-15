'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PageHeader } from '../../../../../components/PageHeader';
import { PeerSelector } from '../../../../../components/PeerSelector';
import { Card } from '../../../../../components/Card';
import { Button } from '../../../../../components/Button';
import { LoadingSpinner } from '../../../../../components/LoadingSpinner';
import { AlertBanner } from '../../../../../components/AlertBanner';

interface Peer {
  id: string;
  name: string;
  role: string;
  department: string;
  email: string;
}

export default function PeerSelectionPage() {
  const params = useParams();
  const router = useRouter();
  const [availablePeers, setAvailablePeers] = useState<Peer[]>([]);
  const [selectedPeers, setSelectedPeers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const MIN_PEERS = 3;
  const MAX_PEERS = 5;

  useEffect(() => {
    const fetchPeers = async () => {
      try {
        const response = await fetch(`/api/employee/evaluations/${params.id}/available-peers`);
        const data = await response.json();
        setAvailablePeers(data.available_peers);
        setSelectedPeers(data.selected_peers || []);
      } catch (error) {
        console.error('Failed to fetch peers:', error);
        setError('Failed to load peer list');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPeers();
  }, [params.id]);

  const handleSubmit = async () => {
    if (selectedPeers.length < MIN_PEERS) {
      setError(`Please select at least ${MIN_PEERS} peers`);
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const response = await fetch(`/api/employee/evaluations/${params.id}/peers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_ids: selectedPeers }),
      });

      if (!response.ok) throw new Error('Failed to save peer selection');

      router.push(`/employee/evaluations/${params.id}`);
    } catch (error) {
      setError('Failed to save peer selection. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Select Peer Reviewers"
        description={`Choose ${MIN_PEERS}-${MAX_PEERS} colleagues who can provide meaningful feedback on your work`}
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'My Evaluations', href: '/employee' },
          { label: 'Evaluation', href: `/employee/evaluations/${params.id}` },
          { label: 'Peer Selection', href: `/employee/evaluations/${params.id}/peer-selection` },
        ]}
      />

      <AlertBanner
        type="info"
        message={`Select peers who have worked closely with you and can provide constructive feedback. You need to select between ${MIN_PEERS} and ${MAX_PEERS} peers.`}
      />

      {error && (
        <AlertBanner type="error" message={error} />
      )}

      <Card className="p-6">
        <div className="mb-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold">
            Available Colleagues
          </h2>
          <div className="text-sm text-gray-600">
            Selected: {selectedPeers.length} / {MAX_PEERS}
          </div>
        </div>

        <PeerSelector
          peers={availablePeers}
          selectedPeers={selectedPeers}
          onSelectionChange={setSelectedPeers}
          minPeers={MIN_PEERS}
          maxPeers={MAX_PEERS}
        />

        <div className="mt-6 flex gap-3 justify-end">
          <Button
            variant="outline"
            onClick={() => router.push(`/employee/evaluations/${params.id}`)}
            disabled={isSaving}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSubmit}
            isLoading={isSaving}
            disabled={selectedPeers.length < MIN_PEERS || selectedPeers.length > MAX_PEERS}
          >
            Submit Selection
          </Button>
        </div>
      </Card>

      {/* Guidelines */}
      <Card className="p-6 bg-blue-50 border-blue-200">
        <h3 className="font-semibold text-blue-900 mb-2">Peer Selection Guidelines</h3>
        <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
          <li>Choose peers who have worked directly with you on projects or tasks</li>
          <li>Select individuals from different teams or functions for diverse perspectives</li>
          <li>Consider peers at various levels who can comment on different aspects of your work</li>
          <li>Avoid selecting only close friends; aim for constructive, honest feedback</li>
          <li>Your manager will review and may adjust your selections</li>
        </ul>
      </Card>
    </div>
  );
}
