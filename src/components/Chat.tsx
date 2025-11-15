'use client';

import { useState } from 'react';
import { ref, push, onValue } from 'firebase/database';
import { rtdb, auth } from '@/lib/firebase';
import { motion } from 'framer-motion';

export default function Chat({ tournamentId }: { tournamentId: string }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [newMsg, setNewMsg] = useState('');

  useEffect(() => {
    const chatRef = ref(rtdb, `chats/${tournamentId}`);
    onValue(chatRef, (snapshot) => {
      const data = snapshot.val();
      setMessages(data ? Object.values(data) : []);
    });
  }, [tournamentId]);

  const sendMsg = () => {
    const user = auth.currentUser;
    if (!user || !newMsg) return;
    push(ref(rtdb, `chats/${tournamentId}`), { text: newMsg, user: user.uid, timestamp: Date.now() });
    setNewMsg('');
  };

  return (
    <motion.div initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="chat chat-start">
      <div className="chat-bubble">
        {messages.map((m, i) => (
          <div key={i}>{m.user}: {m.text}</div>
        ))}
      </div>
      <input value={newMsg} onChange={e => setNewMsg(e.target.value)} className="input" />
      <button onClick={sendMsg} className="btn btn-primary">Send</button>
    </motion.div>
  );
}