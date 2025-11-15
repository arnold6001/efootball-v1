'use client';

import { collection, getDocs, query, orderBy } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

export default function Leaderboard() {
  const [users, setUsers] = useState<any[]>([]);

  useEffect(() => {
    const fetch = async () => {
      const q = query(collection(db, 'userProfiles'), orderBy('wins', 'desc'));
      const snapshot = await getDocs(q);
      setUsers(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    };
    fetch();
  }, []);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="overflow-x-auto">
      <table className="table">
        <thead><tr><th>Rank</th><th>User</th><th>Wins</th><th>Losses</th></tr></thead>
        <tbody>
          {users.map((u, i) => (
            <tr key={u.id}><td>{i+1}</td><td>{u.email || u.id}</td><td>{u.wins}</td><td>{u.losses}</td></tr>
          ))}
        </tbody>
      </table>
    </motion.div>
  );
}