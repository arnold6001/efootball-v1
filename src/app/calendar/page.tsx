'use client';

import { collection, getDocs, query, where } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function Calendar() {
  const [upcoming, setUpcoming] = useState<any[]>([]);

  useEffect(() => {
    const fetch = async () => {
      const q = query(collection(db, 'tournaments'), where('status', '==', 'open'));
      const snapshot = await getDocs(q);
      setUpcoming(snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() })));
    };
    fetch();
  }, []);

  return (
    <div className="container mx-auto p-4">
      <h1>Upcoming Tournaments</h1>
      <ul>
        {upcoming.map(t => (
          <li key={t.id}><Link href={`/tournaments/${t.id}`}>{t.name}</Link></li>
        ))}
      </ul>
    </div>
  );
}