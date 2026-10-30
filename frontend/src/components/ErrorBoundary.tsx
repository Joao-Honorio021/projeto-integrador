import {Component,type ErrorInfo,type ReactNode} from 'react';
/** Mantém uma saída recuperável se uma página falhar durante a renderização. */
export class ErrorBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 componentDidCatch(error:Error,info:ErrorInfo){console.error('Falha de renderização no IndusTrack',error,info.componentStack)}
 render(){return this.state.failed?<div className="empty-state" role="alert"><h2>Não foi possível exibir esta página</h2><p>Recarregue a aplicação para tentar novamente.</p><button onClick={()=>window.location.reload()}>Recarregar</button></div>:this.props.children}
}
