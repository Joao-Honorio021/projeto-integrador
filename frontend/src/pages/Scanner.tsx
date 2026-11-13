import {useEffect,useRef,useState} from 'react';
import {BrowserQRCodeReader,type IScannerControls} from '@zxing/browser';
import {useNavigate} from 'react-router-dom';
import {api,error} from '../services/api';
export default function Scanner(){
 const video=useRef<HTMLVideoElement>(null),controls=useRef<IScannerControls|null>(null),generation=useRef(0);
 const [devices,setDevices]=useState<MediaDeviceInfo[]>([]),[device,setDevice]=useState(''),[message,setMessage]=useState(''),[running,setRunning]=useState(false);
 const navigate=useNavigate();
 function stop(){generation.current++;controls.current?.stop();controls.current=null;setRunning(false)}
 useEffect(()=>()=>{generation.current++;controls.current?.stop()},[]);
 async function start(){stop();const current=++generation.current;setMessage('');setRunning(true);let resolving=false;
 try{const reader=new BrowserQRCodeReader();const streamControls=await reader.decodeFromVideoDevice(device||undefined,video.current!,async result=>{
 if(!result||resolving||current!==generation.current)return;resolving=true;
 try{const url=new URL(result.getText());const match=url.pathname.match(/^\/equipamentos\/([0-9a-f-]{36})\/?$/i);
 if(url.origin!==window.location.origin||!match||url.search||url.hash)throw new Error('Código de outro sistema ou conteúdo inválido.');
 await api.get('/equipamentos/'+match[1]);stop();navigate(url.pathname);
 }catch(reason){setMessage(reason instanceof Error&&!('response' in reason)?reason.message:error(reason));resolving=false}
 });if(current!==generation.current){streamControls.stop();return}controls.current=streamControls;setDevices(await BrowserQRCodeReader.listVideoInputDevices());
 }catch{if(current===generation.current){setRunning(false);setMessage('Não foi possível abrir a câmera. Use HTTPS, permita o acesso e verifique se outra aplicação está usando a câmera.')}}}
 return <article><h2>Ler QR Code</h2><p>Posicione a etiqueta do equipamento diante da câmera.</p><label>Câmera<select value={device} disabled={running} onChange={event=>setDevice(event.target.value)}><option value="">Câmera padrão</option>{devices.map(d=><option value={d.deviceId} key={d.deviceId}>{d.label||'Câmera'}</option>)}</select></label><video ref={video} muted playsInline style={{width:'100%',maxWidth:640}}/><div className="actions"><button disabled={running} onClick={start}>Ativar câmera</button><button disabled={!running} onClick={stop}>Parar câmera</button></div>{message&&<p role="alert">{message}</p>}</article>
}
