'use client';

import { useState } from 'react';
import { doc, updateDoc, getDoc } from 'firebase/firestore';
import { db, auth } from '@/lib/firebase';
import { useRouter } from 'next/navigation';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { motion } from 'framer-motion';

export default function Profile() {
  const [bio, setBio] = useState('');
  const [stats, setStats] = useState({ wins: 0, losses: 0 });
  const router = useRouter();
  const user = auth.currentUser;

  useEffect(() => {
    if (user) {
      getDoc(doc(db, 'userProfiles', user.uid)).then(snap => {
        const data = snap.data();
        setBio(data?.bio || '');
        setStats({ wins: data?.wins || 0, losses: data?.losses || 0 });
      });
    }
  }, [user]);

  const handleUpdate = async () => {
    if (!user) return;
    await updateDoc(doc(db, 'userProfiles', user.uid), { bio });
    router.push('/dashboard');
  };

  return (
    <ProtectedRoute>
      <motion.div className="card w-96 mx-auto mt-20 bg-base-100 shadow-xl">
        <div className="card-body">
          <h2>Profile</h2>
          <p>Wins: {stats.wins} | Losses: {stats.losses}</p>
          <textarea placeholder="Bio" className="textarea textarea-bordered" value={bio} onChange={e => setBio(e.target.value)} />
          <button onClick={handleUpdate} className="btn btn-primary">Update</button>
        </div>
      </motion.div>
    </ProtectedRoute>
  );
}