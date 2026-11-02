export type Country={id:string;iso2:string;name:string;region:string;aggregate:boolean};
export const countryFavoritesKey='quantlabs-worldbank-favorite-countries-v1';
const normalize=(value:string)=>value.normalize('NFD').replace(/\p{Diacritic}/gu,'').toLocaleLowerCase('es');
export function parseCountryFavorites(raw:string|null,items:Country[]):string[]{
 try{const value:unknown=JSON.parse(raw??'[]');if(!Array.isArray(value))return [];const known=new Set(items.map(item=>item.id));return [...new Set(value.filter((id):id is string=>typeof id==='string'&&known.has(id)))];}catch{return [];}
}
export function countryMatches(items:Country[],query:string,favorites:string[],aggregates=false){
 const tokens=normalize(query).split(/\s+/).filter(Boolean);const chosen=new Set(favorites);
 return items.filter(item=>(aggregates||!item.aggregate)&&tokens.every(token=>normalize(`${item.id} ${item.iso2} ${item.name} ${item.region}`).includes(token))).sort((a,b)=>Number(chosen.has(b.id))-Number(chosen.has(a.id))||a.name.localeCompare(b.name,'es')||a.id.localeCompare(b.id));
}
export function toggleCountryFavorite(ids:string[],id:string){return ids.includes(id)?ids.filter(code=>code!==id):[...ids,id];}
