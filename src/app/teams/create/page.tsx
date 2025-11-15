'use client';

import { useState } from 'react';
import { addDoc, collection } from 'firebase/firestore';
import { db, auth } from '@/lib/firebase';
import { useRouter } from 'next/navigation';

export default function CreateTeam() {
  const [name, setName] = useState('');
  const router = useRouter();

  const handleCreate = async () => {
    const user = auth.currentUser;
    if (!user) return;
    await addDoc(collection(db, 'teams'), { name, creatorId: user.uid, members: [user.uid] });
    router.push('/dashboard');
  };

  return (
    <div className="card w-96 mx-auto mt-20">
      <input value={name} onChange={e => setName(e.target.value)} placeholder="Team Name" />
      <button onClick={handleCreate}>Create Team</button>
    </div>
  );
}