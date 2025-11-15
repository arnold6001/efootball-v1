// ... import Chat
// Add format selection in generateFixtures

const generateFixtures = async () => {
  // ... existing for single-elim
  if (tournament.format === 'round-robin') {
    // Simple round-robin: every vs every
    const matches = [];
    for (let i = 0; i < tournament.players.length; i++) {
      for (let j = i + 1; j < tournament.players.length; j++) {
        matches.push({
          id: matches.length,
          participants: [tournament.players[i], tournament.players[j]],
          state: 'NO_SHOW',
        });
      }
    }
    // Update bracket
  }
  // After match update, update profiles wins/losses
  // e.g., winner wins++, loser losses++
  // Push notification: push(ref(rtdb, `notifications/${userId}`), {msg: 'Match updated!'});
};

// Add to return:
<Chat tournamentId={params.id} />
// Add analytics section: List past matches for user