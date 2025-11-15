import { ProtectedRoute } from '@/components/ProtectedRoute';
import Leaderboard from '@/components/Leaderboard';

export default function LeaderboardPage() {
  return (
    <ProtectedRoute>
      <div className="container mx-auto p-4">
        <h1 className="text-3xl font-bold mb-4">Global Leaderboard</h1>
        <Leaderboard />
      </div>
    </ProtectedRoute>
  );
}