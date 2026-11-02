import type {Project,ProjectNode,NodeResult} from './model';
export type Coefficient={term:string;estimate:number;std_error?:number;p_value?:number;ci_low?:number;ci_high?:number};
export type Regression={y:string;features:string[];coefficients:Coefficient[];n?:number;dropped?:number;r_squared?:number;r_squared_adj?:number;aic?:number;bic?:number;covariance?:string};
export const isRegression=(node:ProjectNode|undefined)=>node?.type==='ols'||node?.type==='multiple_ols';
export function chooseRegression(project:Project,selectedId:string,activeId=''){
 return [project.nodes.find(node=>node.id===selectedId),project.nodes.find(node=>node.id===activeId),...project.nodes].find(node=>isRegression(node));
}
export function regressionData(node:ProjectNode|undefined,state:NodeResult|undefined):Regression|undefined{
 if(!isRegression(node)||state?.status!=='succeeded'||!state.result)return;
 const result=state.result;
 if(node!.type==='ols'&&Array.isArray(result.coefficients))return {...result,y:String(result.y),features:[String(result.x)]} as unknown as Regression;
 if(node!.type==='multiple_ols'&&result.regression)return result.regression as Regression;
}
export function fittedEquation(data:Regression|undefined){
 if(!data)return;
 const intercept=data.coefficients.find(row=>row.term==='const')?.estimate;
 if(typeof intercept!=='number'||!Number.isFinite(intercept))return;
 const terms=data.features.map(name=>({name,value:data.coefficients.find(row=>row.term===name)?.estimate}));
 if(terms.some(term=>typeof term.value!=='number'||!Number.isFinite(term.value)))return;
 return {intercept,terms:terms as {name:string;value:number}[]};
}
