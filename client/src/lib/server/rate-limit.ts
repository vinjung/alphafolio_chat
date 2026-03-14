/**
 * @class TokenBucket
 * @description 토큰 버킷 알고리즘을 구현한 클래스입니다. 요청 속도 제한(rate limiting)에 사용됩니다.
 * @template _Key - 버킷을 식별하는 키의 타입
 */
export class TokenBucket<_Key> {
  /**
   * @property {number} max - 버킷의 최대 토큰 수
   */
  public max: number;

  /**
   * @property {number} refillIntervalSeconds - 토큰이 리필되는 시간 간격(초)
   */
  public refillIntervalSeconds: number;

  /**
   * @constructor
   * @param {number} max - 버킷의 최대 토큰 수
   * @param {number} refillIntervalSeconds - 토큰이 리필되는 시간 간격(초)
   */
  constructor(max: number, refillIntervalSeconds: number) {
    this.max = max;
    this.refillIntervalSeconds = refillIntervalSeconds;
  }

  /**
   * @private
   * @property {Map<_Key, Bucket>} storage - 키별 버킷 저장소
   */
  private storage = new Map<_Key, Bucket>();

  /**
   * @method check
   * @description 주어진 키에 대해 지정된 비용만큼의 토큰을 사용할 수 있는지 확인합니다.
   * @param {_Key} key - 확인할 버킷의 키
   * @param {number} cost - 사용할 토큰의 수
   * @returns {boolean} - 토큰을 사용할 수 있으면 true, 그렇지 않으면 false
   */
  public check(key: _Key, cost: number): boolean {
    const bucket = this.storage.get(key) ?? null;
    if (bucket === null) {
      return true;
    }
    const now = Date.now();
    const refill = Math.floor(
      (now - bucket.refilledAt) / (this.refillIntervalSeconds * 1000)
    );
    if (refill > 0) {
      return Math.min(bucket.count + refill, this.max) >= cost;
    }
    return bucket.count >= cost;
  }

  /**
   * @method consume
   * @description 주어진 키에 대해 지정된 비용만큼의 토큰을 소비합니다.
   * @param {_Key} key - 토큰을 소비할 버킷의 키
   * @param {number} cost - 소비할 토큰의 수
   * @returns {boolean} - 토큰 소비에 성공하면 true, 실패하면 false
   */
  public consume(key: _Key, cost: number): boolean {
    let bucket = this.storage.get(key) ?? null;
    const now = Date.now();
    if (bucket === null) {
      bucket = {
        count: this.max - cost,
        refilledAt: now,
      };
      this.storage.set(key, bucket);
      return true;
    }
    const refill = Math.floor(
      (now - bucket.refilledAt) / (this.refillIntervalSeconds * 1000)
    );
    if (refill > 0) {
      bucket.count = Math.min(bucket.count + refill, this.max);
      bucket.refilledAt = now;
    }
    if (bucket.count < cost) {
      this.storage.set(key, bucket);
      return false;
    }
    bucket.count -= cost;
    this.storage.set(key, bucket);
    return true;
  }
}
/**
 * @interface Bucket
 * @description 버킷의 상태를 저장하기 위한 인터페이스
 */
interface Bucket {
  /**
   * @property {number} count - 현재 버킷에 남아있는 토큰의 수
   */
  count: number;

  /**
   * @property {number} refilledAt - 마지막으로 토큰이 리필된 시간(밀리초)
   */
  refilledAt: number;
}
