'use client';

import { ServiceSuspensionModal } from '@/components/shared/service-suspension-modal';
import { useState, useEffect } from 'react';

export function ServiceSuspensionModalWrapper() {
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    setShowModal(true);
  }, []);

  return (
    <ServiceSuspensionModal 
      isVisible={showModal} 
      onCloseAction={() => setShowModal(false)} 
    />
  );
}