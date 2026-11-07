import { DRAFT_TRADE_DETAIL as TUNING } from './constants-draft-motion.mjs';
import { BADGE } from "./constants-draft-motion.mjs";
export { BADGE };
import * as THREE from 'three';
import { PALETTE } from './constants.mjs';
import { BOARD, CARD_HEIGHT } from './draft-board.mjs';
import { TEAM_NAME, teamName } from './draft-textures.mjs';
import { tradePlaces } from './draft-beats.mjs';
import { FILM_COPY } from './film-copy.mjs';

/* The trade's two props (revision 15). Aura's badge stands off the board, left of its edge: the team's
   avatar large in a white rim with its name under it, so the card lands at a team, not in a column. The
   cover is a strip in the card's own print colour over its "WR · 2.12" tag, faded in before the WR111
   stamp slams onto the same spot (draft-beats.mjs TRADED). */

const basic = options => new THREE.MeshBasicMaterial({toneMapped: false, transparent: true, depthWrite: false, ...options});

/* Builds the badge on the board and the cover on the card; returns the trade's places (tradePlaces). */
export function tradeProps(item, draft, board, add) {
  const trade = draft.beats.traded.path.find(step => step.kind === 'trade');
  const places = tradePlaces(item.home), badge = new THREE.Group();
  const rim = new THREE.Mesh(new THREE.CircleGeometry(BADGE.avatar + BADGE.rim, TUNING.avatarSegments), basic({color: PALETTE.white}));
  const face = new THREE.Mesh(new THREE.CircleGeometry(BADGE.avatar, TUNING.avatarSegments), board.headers.get(trade.team).disc.material);
  face.position.z = TUNING.faceZ;
  const name = new THREE.Mesh(new THREE.PlaneGeometry(BADGE.nameWidth, BADGE.nameWidth * TEAM_NAME.height / TEAM_NAME.width),
    basic({map: teamName(FILM_COPY.team[trade.team])}));
  name.position.y = -BADGE.nameBelow;
  badge.add(rim, face, name);
  badge.position.copy(places.badge); badge.visible = false;
  board.group.add(badge);
  const {width, height, y, behind} = BADGE.cover;
  const cover = new THREE.Mesh(new THREE.PlaneGeometry(BOARD.card * width, CARD_HEIGHT * height), basic({color: PALETTE.print, opacity: 0}));
  cover.position.set(0, CARD_HEIGHT * y, item.props.stampZ - behind); cover.visible = false;
  add(item, cover);
  Object.assign(item.props, {badge, cover});
  return places;
}
