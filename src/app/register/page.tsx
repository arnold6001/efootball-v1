// ... same, but after register:
await setDoc(doc(db, 'userProfiles', userCredential.user.uid), { email, wins: 0, losses: 0, rank: 0, bio: '' });