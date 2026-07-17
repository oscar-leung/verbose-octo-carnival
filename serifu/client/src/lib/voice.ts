import type { SignalData } from '../../../shared/types';

const ICE_SERVERS: RTCIceServer[] = [{ urls: 'stun:stun.l.google.com:19302' }];

interface PeerConn {
  pc: RTCPeerConnection;
  polite: boolean;
  makingOffer: boolean;
  ignoreOffer: boolean;
  /** Serializes async signal handling per peer to avoid SDP races. */
  queue: Promise<void>;
}

/**
 * Full-mesh audio between everyone in the room who joined voice.
 * Uses the MDN "perfect negotiation" pattern; politeness is decided by
 * comparing socket ids so both sides always disagree about who yields.
 */
export class VoiceMesh {
  private peers = new Map<string, PeerConn>();
  private localStream: MediaStream | null = null;
  private muted = false;

  constructor(
    private selfId: string,
    private sendSignal: (to: string, data: SignalData) => void,
    private onStream: (peerId: string, stream: MediaStream | null) => void
  ) {}

  get active(): boolean {
    return this.localStream !== null;
  }

  async start(): Promise<void> {
    if (this.localStream) return;
    this.localStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      video: false,
    });
    this.applyMute();
  }

  stop(): void {
    for (const peerId of [...this.peers.keys()]) this.removePeer(peerId);
    this.localStream?.getTracks().forEach((t) => t.stop());
    this.localStream = null;
  }

  setMuted(muted: boolean): void {
    this.muted = muted;
    this.applyMute();
  }

  private applyMute(): void {
    this.localStream?.getAudioTracks().forEach((t) => {
      t.enabled = !this.muted;
    });
  }

  /** Reconcile connections against the current set of in-voice peers. */
  syncPeers(peerIds: string[]): void {
    if (!this.localStream) return;
    const want = new Set(peerIds.filter((id) => id !== this.selfId));
    for (const id of [...this.peers.keys()]) {
      if (!want.has(id)) this.removePeer(id);
    }
    for (const id of want) {
      if (!this.peers.has(id)) this.addPeer(id);
    }
  }

  handleSignal(from: string, data: SignalData): void {
    if (!this.localStream) return;
    let peer = this.peers.get(from);
    if (!peer) {
      // The other side joined voice and reached us before our roster update.
      peer = this.addPeer(from);
    }
    const p = peer;
    p.queue = p.queue.then(() => this.processSignal(from, p, data)).catch((err) => {
      console.error('[voice] signal handling failed', err);
    });
  }

  private async processSignal(from: string, peer: PeerConn, data: SignalData): Promise<void> {
    const { pc } = peer;
    if (data.description) {
      const description = data.description as RTCSessionDescriptionInit;
      const collision =
        description.type === 'offer' && (peer.makingOffer || pc.signalingState !== 'stable');
      peer.ignoreOffer = !peer.polite && collision;
      if (peer.ignoreOffer) return;
      await pc.setRemoteDescription(description);
      if (description.type === 'offer') {
        await pc.setLocalDescription();
        this.sendSignal(from, { description: pc.localDescription?.toJSON() ?? null });
      }
    } else if (data.candidate) {
      try {
        await pc.addIceCandidate(data.candidate as RTCIceCandidateInit);
      } catch (err) {
        if (!peer.ignoreOffer) console.error('[voice] addIceCandidate failed', err);
      }
    }
  }

  private addPeer(peerId: string): PeerConn {
    const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
    const peer: PeerConn = {
      pc,
      polite: this.selfId > peerId,
      makingOffer: false,
      ignoreOffer: false,
      queue: Promise.resolve(),
    };
    this.peers.set(peerId, peer);

    if (this.localStream) {
      for (const track of this.localStream.getTracks()) {
        pc.addTrack(track, this.localStream);
      }
    }

    pc.onnegotiationneeded = async () => {
      try {
        peer.makingOffer = true;
        await pc.setLocalDescription();
        this.sendSignal(peerId, { description: pc.localDescription?.toJSON() ?? null });
      } catch (err) {
        console.error('[voice] negotiation failed', err);
      } finally {
        peer.makingOffer = false;
      }
    };
    pc.onicecandidate = ({ candidate }) => {
      if (candidate) this.sendSignal(peerId, { candidate: candidate.toJSON() as Record<string, unknown> });
    };
    pc.ontrack = (event) => {
      const stream = event.streams[0] ?? new MediaStream([event.track]);
      this.onStream(peerId, stream);
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === 'failed') pc.restartIce();
      if (pc.connectionState === 'closed' || pc.connectionState === 'disconnected') {
        // Roster sync will clean up if the peer actually left.
      }
    };
    return peer;
  }

  private removePeer(peerId: string): void {
    const peer = this.peers.get(peerId);
    if (!peer) return;
    this.peers.delete(peerId);
    peer.pc.onnegotiationneeded = null;
    peer.pc.onicecandidate = null;
    peer.pc.ontrack = null;
    peer.pc.close();
    this.onStream(peerId, null);
  }
}
