function Loader({ width, height }) {
    return (
        <div
            style={{
                width: `${width}px`,
                height: `${height}px`,
                border: '2px solid #f3f3f3',
                borderTop: '2px solid #3498db',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite',
            }}
        ></div>
    );
};

export default Loader;